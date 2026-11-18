# Agent workspace image. The grader, reference and cheats are NOT copied in.
# Build:  docker build -t t2_glob_doublestar .        Run:  docker run --rm -it --network none t2_glob_doublestar
FROM python:3.11-slim
RUN useradd -m agent
WORKDIR /workspace
COPY --chown=agent:agent . /workspace
RUN rm -f /workspace/Dockerfile
USER agent
CMD ["bash"]
