import socket
import threading
import queue
import argparse
import yaml
import cv2
import numpy as np
from ultralytics import YOLO
import time


def create_client_socket(transmission_cfg, server_cfg):
    """Cria um socket UDP ou TCP dependendo da configuração."""
    protocol = cfg.get("protocol", "udp").lower()

    if protocol == "udp":
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.setsockopt(
            socket.SOL_SOCKET, socket.SO_RCVBUF, server_cfg["buffer_size"]
        )
        client.bind((transmission_cfg["host"], transmission_cfg["port"]))
        return client
    elif protocol == "tcp":
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_cfg["host"], server_cfg["port"]))
        return client
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")


def enviar_mensagens(fila, cfg, server_cfg):
    """Thread responsável por enviar as mensagens (imagens ou dados)."""
    protocol = cfg.get("protocol", "udp").lower()
    server_addr = (server_cfg["host"], server_cfg["port"])

    if protocol == "udp":
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            item = fila.get()
            if item is None:
                break
            try:
                sock.sendto(item["header"], server_addr)
                sock.sendto(item["buff"], server_addr)
            except Exception as e:
                print(f"[ERRO][UDP]: {e}")
    elif protocol == "tcp":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(server_addr)
            while True:
                item = fila.get()
                if item is None:
                    break
                try:
                    sock.sendall(item["header"] + item["buff"])
                except Exception as e:
                    print(f"[ERRO][TCP]: {e}")
    else:
        print(
            f"[ERRO] Protocolo '{protocol}' ainda não implementado (ex: gRPC/WebRTC)."
        )


def obj_detect(command_ref, fila, video_path, model_cfg, name):
    """Thread de detecção de objetos."""
    cam = cv2.VideoCapture(video_path)
    model = YOLO(model_cfg["path"], task="detect")

    model.overrides.update(
        {
            "conf": model_cfg.get("conf", 0.7),
            "agnostic_nms": model_cfg.get("agnostic_nms", True),
            "single_cls": model_cfg.get("single_cls", True),
            "classes": model_cfg.get("classes", [0]),
        }
    )

    bytes_name = name.encode("utf-8").ljust(32, b"\0")

    frame_count = 0
    frame_freq = model_cfg.get("frame_freq", 15)

    try:
        while command_ref["state"] == "start":
            frame_count += 1
            if frame_count % frame_freq != 0:
                continue

            ret, img = cam.read()

            if not ret:
                break

            results = model(img)
            for result in results:
                if not result.boxes:
                    continue

                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()

                for box, confidence in zip(boxes, confidences):
                    if confidence > model_cfg.get("conf", 0.7):
                        box = np.intp(box)
                        _, buffer = cv2.imencode(
                            ".jpg", img[box[1] : box[3], box[0] : box[2]]
                        )
                        size = len(buffer)
                        size_bytes = str(size).zfill(4).encode("utf-8")
                        header = bytes_name + size_bytes
                        fila.put({"header": header, "buff": buffer})
            # time.sleep(0.05)
    finally:
        cam.release()
        print("[INFO] Captura finalizada.")


def run_instance(instance_cfg, cfg):
    """Executa uma instância completa de leitura e envio."""
    transmission_cfg = instance_cfg["transmission"]
    server_cfg = cfg["server"]
    client = create_client_socket(transmission_cfg, server_cfg)
    command_ref = {"state": "wait"}
    fila = queue.Queue()

    # Threads
    detect_thread = threading.Thread(
        target=obj_detect,
        args=(
            command_ref,
            fila,
            instance_cfg["video"],
            cfg["model"],
            instance_cfg["name"],
        ),
    )
    send_thread = threading.Thread(
        target=enviar_mensagens, args=(fila, cfg, server_cfg)
    )

    print(f"[INFO] Instância '{instance_cfg['name']}' iniciada. Aguardando comandos...")
    while command_ref["state"] != "exit":
        msg = client.recv(64).decode()
        if len(msg) > 0:
            print(f"[{instance_cfg['name']}] Mensagem recebida: {msg}")
            if msg == "start" and command_ref["state"] != msg:
                command_ref["state"] = msg
                detect_thread.start()
                send_thread.start()
            elif msg == "exit":
                command_ref["state"] = msg
                fila.put(None)
                detect_thread.join()
                send_thread.join()
                print(f"[INFO] Instância '{instance_cfg['name']}' finalizada.")
            elif msg == "warmup":
                print("[INFO] Warmup iniciado")
                count = 0
                while count < 30:
                    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                    h, w, _ = img.shape
                    box = np.array(
                        [
                            w // 2 - 100,  # x1
                            h // 2 - 100,  # y1
                            w // 2 + 100,  # x2
                            h // 2 + 100,  # y2
                        ]
                    )

                    box = np.intp(box)

                    _, buffer = cv2.imencode(
                        ".jpg", img[box[1] : box[3], box[0] : box[2]]
                    )

                    size = len(buffer)
                    header = f"{size}\0".encode("utf-8")
                    # fila.put({"header": header, "buff": buffer})
                    count += 1
                    time.sleep(0.05)
                print("[INFO] Warmup finalizado")


def main(cfg):
    threads = []
    for instance_cfg in cfg["instances"]:
        t = threading.Thread(target=run_instance, args=(instance_cfg, cfg))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--source-config-file",
        default="./config.yaml",
        help="Input your config.yaml file",
    )
    args = parser.parse_args()

    with open(args.source_config_file, "r") as f:
        cfg = yaml.safe_load(f)

    main(cfg)
