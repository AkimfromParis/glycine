#!/bin/sh
echo "Starting Ollama..."
ollama serve &

# Wait for Ollama to become available
echo "Waiting for Ollama to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
  sleep 1
done

echo "Pulling model qwen2:3b-instruct..."
ollama pull qwen2.5:3b-instruct
# Keep the container running
wait