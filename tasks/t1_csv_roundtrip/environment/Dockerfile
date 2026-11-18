# Agent workspace image. The grader, reference and cheats are NOT copied in.
# Build:  docker build -t t1_csv_roundtrip .        Run:  docker run --rm -it --network none t1_csv_roundtrip
FROM python:3.11-slim
RUN useradd -m agent
WORKDIR /workspace
COPY --chown=agent:agent . /workspace
RUN rm -f /workspace/Dockerfile
USER agent
CMD ["bash"]
