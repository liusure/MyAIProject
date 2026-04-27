#!/bin/bash
set -e

echo "=== 1. 启动 minikube（如果还没启动）==="
minikube status >/dev/null 2>&1 || minikube start

echo "=== 2. 切换到 minikube 的 Docker 环境 ==="
eval $(minikube docker-env)

echo "=== 3. 构建镜像 ==="
docker build -t course-backend:latest ./backend
docker build -t course-frontend:latest ./frontend

echo "=== 4. 部署到 K8s ==="
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

echo "=== 5. 等待 Pod 启动 ==="
kubectl wait --for=condition=ready pod -l app=postgres -n course-select --timeout=60s
kubectl wait --for=condition=ready pod -l app=redis -n course-select --timeout=60s
kubectl wait --for=condition=ready pod -l app=backend -n course-select --timeout=60s
kubectl wait --for=condition=ready pod -l app=frontend -n course-select --timeout=60s

echo "=== 6. 部署完成！==="
echo ""
kubectl get all -n course-select
echo ""
echo "访问地址："
minikube service frontend-svc -n course-select --url
