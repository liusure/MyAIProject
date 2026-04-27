#!/bin/bash
set -e

echo "删除所有 K8s 资源..."
kubectl delete namespace course-select

echo "停止 minikube..."
minikube stop

echo "清理完成！"
