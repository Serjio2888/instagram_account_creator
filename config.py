import os

GRPC_HOST = (
    "localhost:50551" if "GRPC_HOST" not in os.environ else os.environ.get("GRPC_HOST")
)
