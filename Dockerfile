FROM python:3.12-slim
RUN pip install --no-cache-dir manifold3d==3.5.4 numpy==2.5.3 shapely==2.2.0 trimesh==5.1.1 matplotlib==3.11.2
