.PHONY: proto run dev

# Compile gRPC Python stubs from chat.proto
proto:
	python -m grpc_tools.protoc -I app/chat/proto \
		--python_out=app/chat/proto --grpc_python_out=app/chat/proto \
		app/chat/proto/chat.proto

# Hot‑reload FastAPI server (local dev)
run:
	uvicorn app.main:app --reload --port 8000

# One command to regenerate stubs then start the server
dev: proto run