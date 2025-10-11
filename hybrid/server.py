import socket
import threading
import cv2
import numpy as np
import struct
import yaml
import time
import logging
import errno
import os
from datetime import datetime
from scipy.spatial import distance
from deep_sort_realtime.deepsort_tracker import DeepSort


class PersonReidentificationServer:
    def __init__(self, config_path="config.yaml"):
        self.detectedPersons = {}
        self.threads = []
        self.clients = []
        self.lines = []
        self.id_counter = 0
        self.command = "wait"
        self.server = None
        self.server_lock = threading.Lock()
        self.tracker = None
        self.cfg = None
        self.config_path = config_path
        self.running = False
        self.logger = None

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(
            log_dir, f"server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file)],
        )
        self.logger = logging.getLogger("PersonReIDServer")
        # self.logger.propagate = False

    def load_config(self):
        """Load configuration from YAML file"""
        if self.logger is None:
            return

        try:
            with open(self.config_path, "r") as f:
                self.cfg = yaml.safe_load(f)
            self.logger.info("Configuration loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return False

    def get_clients(self):
        """Extract client configurations from config"""
        if self.cfg is None:
            return

        clients = []
        for instance_cfg in self.cfg["instances"]:
            clients.append(instance_cfg["transmission"])
        return clients

    def initialize(self):
        """Initialize server components"""
        self.setup_logging()

        if not self.load_config():
            return False

        if self.cfg is None or self.logger is None:
            return

        netcfg = self.cfg["server"]
        server_host = netcfg.get("host", "0.0.0.0")
        server_port = netcfg.get("port", 5000)

        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # On Linux, you might need SO_REUSEPORT instead
            try:
                self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                pass  # SO_REUSEPORT not available on this platform

            self.server.bind((server_host, server_port))
            self.logger.info(f"UDP server bound to {server_host}:{server_port}")
        except Exception as e:
            self.logger.error(f"Failed to initialize server socket: {e}")
            return False

        self.clients = self.get_clients()
        self.logger.info(
            f"Loaded {len(self.clients) if self.clients is not None else []} clients from configuration"
        )

        reid_cfg = self.cfg.get("reid", {})
        try:
            self.tracker = DeepSort(
                max_age=reid_cfg.get("max_age", 10),
                n_init=reid_cfg.get("n_init", 3),
                nn_budget=reid_cfg.get("nn_budget", 100),
            )
            self.logger.info("DeepSort tracker initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize DeepSort tracker: {e}")
            return False

        return True

    def broadcast(self, message):
        """Send message to all configured clients"""

        if self.logger is None or self.clients is None:
            return

        with self.server_lock:
            if self.server is None:
                self.logger.warning("Server not initialized for broadcast")
                return

            success_count = 0
            for client in self.clients:
                try:
                    self.server.sendto(
                        message.encode(), (client["host"], client["port"])
                    )
                    success_count += 1
                    self.logger.debug(
                        f"Broadcast '{message}' to {client['host']}:{client['port']}"
                    )
                except socket.error as e:
                    if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                        self.logger.warning(
                            f"Resource temporarily unavailable for {client['host']}:{client['port']}"
                        )
                        continue
                    else:
                        self.logger.error(
                            f"Error notifying {client['host']}:{client['port']}: {e}"
                        )
                except Exception as e:
                    self.logger.error(
                        f"Unexpected error broadcasting to {client['host']}:{client['port']}: {e}"
                    )

            self.logger.info(
                f"Broadcast '{message}' completed: {success_count}/{len(self.clients)} clients"
            )

    def add_new_person(self, extractedFeature, frame, addr):
        """Add new person to the gallery"""
        if self.logger is None:
            return

        pid = self.id_counter
        self.detectedPersons[f"id_{pid}"] = {
            "extractedFeatures": extractedFeature,
            "id": pid,
            "appearances": 1,
            "first_seen": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
        }

        _, port = addr
        self.id_counter += 1

        self.logger.info(f"New person id_{pid} registered from {addr}")
        return pid

    def reId(self, frame, addr):
        """
        Re-identification logic using DeepSORT for embedding extraction
        """
        if self.logger is None or self.tracker is None or self.cfg is None:
            return

        try:
            _, port = addr

            h, w = frame.shape[:2]
            detections = [([0, 0, w, h], 1.0, "person")]

            tracks = self.tracker.update_tracks(detections, frame=frame)

            embedding = None
            for tr in tracks:
                if tr.features and len(tr.features) > 0:
                    embedding = np.asarray(tr.features[-1], dtype=np.float32)
                    break

            if embedding is None:
                embedding = np.mean(frame, axis=(0, 1)).astype(np.float32)
                embedding = embedding.flatten()
                self.logger.debug("Used fallback feature extraction")

            embedding = embedding.flatten()

            if not self.detectedPersons:
                pid = self.add_new_person(
                    np.expand_dims(embedding, axis=0), frame, addr
                )
                self.lines.append(f"{pid} {port} 1\n")
                self.logger.info(f"First person id_{pid} registered from {addr}")
                return

            candidates = []
            for key, value in self.detectedPersons.items():
                gallery = value["extractedFeatures"]
                if gallery.ndim == 1:
                    gallery_mean = gallery
                else:
                    gallery_mean = np.mean(gallery, axis=0).flatten()
                score = distance.cosine(gallery_mean, embedding.flatten())
                candidates.append(
                    {
                        "id": value["id"],
                        "appearances": value["appearances"],
                        "score": float(score),
                    }
                )

            candidates_sorted = sorted(candidates, key=lambda d: d["score"])
            top = candidates_sorted[0]

            sim_thresh = self.cfg["reid"].get("similarity_threshold", 0.13)
            max_gallery = self.cfg["reid"].get("max_gallery_per_person", 512)

            if top["score"] < sim_thresh:
                person_key = f"id_{top['id']}"
                current_gallery = self.detectedPersons[person_key]["extractedFeatures"]
                if current_gallery.ndim == 1:
                    current_gallery = np.expand_dims(current_gallery, axis=0)

                if current_gallery.shape[0] < max_gallery:
                    new_gallery = np.vstack(
                        (current_gallery, np.expand_dims(embedding, axis=0))
                    )
                else:
                    new_gallery = np.vstack(
                        (np.expand_dims(embedding, axis=0), current_gallery[1:])
                    )

                self.detectedPersons[person_key] = {
                    "extractedFeatures": new_gallery,
                    "id": top["id"],
                    "appearances": top["appearances"] + 1,
                    "first_seen": self.detectedPersons[person_key]["first_seen"],
                    "last_seen": datetime.now().isoformat(),
                }
                self.lines.append(f"{top['id']} {port} {top['appearances'] + 1}\n")
                self.logger.info(
                    f"Matched existing person id_{top['id']} (score={top['score']:.4f}) from {addr}"
                )
            else:
                pid = self.add_new_person(
                    np.expand_dims(embedding, axis=0), frame, addr
                )
                self.lines.append(f"{pid} {port} 1\n")
                self.logger.info(
                    f"New person id_{pid} created (best match score={top['score']:.4f}) from {addr}"
                )

        except Exception as e:
            self.logger.error(f"Exception processing frame from {addr}: {e}")

    def handle_client(self):
        """Thread that receives frames while command == 'start'"""
        # TODO: Por algum motivo eu to com tendo um delay e o sevidor não recebe as primeiras requisições
        if self.logger is None or self.cfg is None:
            return

        buffer_timeout = self.cfg["server"].get("socket_timeout", 2)

        with self.server_lock:
            if self.server is None:
                self.logger.error("Server socket is None in handle_client")
                return
            self.server.settimeout(buffer_timeout)

        self.logger.info("Client handler thread started")
        consecutive_errors = 0
        max_consecutive_errors = 10

        while self.command == "start" and self.running:
            try:
                size_data, addr = self.server.recvfrom(4)
                if len(size_data) < 4:
                    self.logger.warning("Received invalid size header")
                    continue
                size = struct.unpack("!I", size_data)[0]

                buffer, addr = self.server.recvfrom(size)
                if not buffer:
                    continue

                frame = cv2.imdecode(
                    np.frombuffer(buffer, dtype=np.uint8), cv2.IMREAD_COLOR
                )
                if frame is None:
                    self.logger.warning(f"Could not decode image from {addr}")
                    continue

                consecutive_errors = 0

                t = threading.Thread(target=self.reId, args=(frame, addr))
                t.daemon = True
                self.threads.append(t)
                t.start()

            except socket.timeout:
                continue
            except socket.error as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    self.logger.warning(
                        "Resource temporarily unavailable in socket operation"
                    )
                    time.sleep(0.1)
                    continue
                elif not self.running:
                    break
                else:
                    consecutive_errors += 1
                    self.logger.error(f"Socket error in handle_client: {e}")
                    if consecutive_errors >= max_consecutive_errors:
                        self.logger.error(
                            "Too many consecutive socket errors, breaking handler loop"
                        )
                        break
                    time.sleep(0.5)
            except Exception as e:
                if not self.running:
                    break
                consecutive_errors += 1
                self.logger.error(f"Unexpected error in handle_client: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error(
                        "Too many consecutive errors, breaking handler loop"
                    )
                    break
                time.sleep(0.5)

        self.logger.info("Client handler thread stopped")

    def cleanup_threads(self):
        """Clean up finished threads"""
        self.threads = [t for t in self.threads if t.is_alive()]

    def start_processing(self):
        """Start the processing loop"""
        if self.logger is None:
            return

        if self.command == "start":
            self.logger.warning("Processing already started")
            return

        self.command = "start"
        self.broadcast(self.command)

        self.cleanup_threads()

        t = threading.Thread(target=self.handle_client)
        t.daemon = True
        self.threads.append(t)
        t.start()
        self.logger.info("Processing started - handler thread launched")

    def stop_processing(self):
        """Stop the processing loop and clean up"""
        if self.logger is None:
            return

        self.command = "exit"
        self.running = False

        self.broadcast(self.command)

        self.logger.info(f"Waiting for {len(self.threads)} threads to finish...")

        for i, t in enumerate(self.threads):
            try:
                t.join(timeout=2.0)
                if t.is_alive():
                    self.logger.warning(f"Thread {i} did not finish in time")
            except Exception as e:
                self.logger.error(f"Error joining thread {i}: {e}")

        self.threads.clear()

        with self.server_lock:
            if self.server:
                try:
                    self.server.close()
                    self.server = None
                    self.logger.info("Server socket closed")
                except Exception as e:
                    self.logger.error(f"Error closing server socket: {e}")

        try:
            with open("example.txt", "w") as f:
                f.writelines(self.lines)
            self.logger.info(
                f"Results written to example.txt with {len(self.lines)} entries"
            )
        except Exception as e:
            self.logger.error(f"Error writing results to file: {e}")

    def get_status(self):
        """Get current server status"""
        self.cleanup_threads()
        return {
            "command": self.command,
            "detected_persons": len(self.detectedPersons),
            "active_threads": len([t for t in self.threads if t.is_alive()]),
            "total_reid_events": len(self.lines),
            "clients_configured": len(self.clients) if self.clients is not None else [],
            "id_counter": self.id_counter,
        }

    def run(self):
        """Main server loop"""
        if not self.initialize():
            print("[ERROR] Fail initializing")
            return

        if self.logger is None:
            return

        self.logger.info("Initializing Person Re-identification Server...")

        self.running = True

        self.logger.info("Server started - ready for commands")
        print(
            "Server started... (type 'start' to begin processing, 'exit' to quit, 'status' for info)"
        )

        try:
            while self.running:
                cmd = input("server@command# ").strip().lower()
                self.logger.info(f"User command: {cmd}")

                if cmd == "start":
                    self.start_processing()

                elif cmd == "exit":
                    self.logger.info("Shutdown command received")
                    self.stop_processing()
                    break

                elif cmd == "status":
                    status = self.get_status()
                    print("\n=== Server Status ===")
                    print(f"Command State: {status['command']}")
                    print(f"Detected Persons: {status['detected_persons']}")
                    print(f"Active Threads: {status['active_threads']}")
                    print(f"ReID Events: {status['total_reid_events']}")
                    print(f"Clients Configured: {status['clients_configured']}")
                    print(f"Next ID: {status['id_counter']}")
                    print("====================\n")

                elif cmd == "cleanup":
                    self.cleanup_threads()
                    print("Thread cleanup completed")

                else:
                    print(
                        "Unknown command. Use 'start', 'exit', 'status', or 'cleanup'."
                    )

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            print("\nKeyboard interrupt received. Shutting down...")
            self.stop_processing()
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
            self.stop_processing()

        self.logger.info("Server stopped")


if __name__ == "__main__":
    server = PersonReidentificationServer("config.yaml")
    server.run()
