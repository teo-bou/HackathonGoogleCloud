# Use micromamba image (small) with conda-forge support
FROM mambaorg/micromamba:1.4.0

# Set workdir
WORKDIR /workspace

# Ensure conda-installed binaries are on PATH at runtime (python, streamlit, pip, etc.)
ENV PATH=/opt/conda/bin:${PATH}

# Create environment and install python + geopandas dependencies
# Use conda-forge channel for GIS stack
RUN micromamba install -y -n base -c conda-forge \
    python=3.11 \
    pip \
    geopandas \
    fiona \
    gdal \
    shapely \
    pyproj \
    rtree \
    matplotlib \
    pandas \
    -c conda-forge && micromamba clean --all --yes

# Copy project files (pip install will read requirements.txt)
COPY . /workspace

# Use micromamba to run pip inside the conda environment so the 'pip' binary is available
# Install python dependencies via pip
RUN micromamba install -y -n base pip && \
    /opt/conda/bin/pip install -r requirements.txt

# Expose the ports used by ADK API and Streamlit
EXPOSE 8000 8501

# Note: the micromamba base image may not run as root during build, so creating
# a new user with `useradd` can fail. For simplicity we keep running as the
# default user provided by the base image during build. If you need a non-root
# user at runtime, create it in the container entrypoint or adjust the base
# image to one that allows root operations during build.

# Default command: 'docker-compose' will control services.
# Provide a simple entrypoint: by default start nothing, user should run via docker-compose
CMD ["bash", "-lc", "echo 'Image built. Use docker-compose to run the ADK API and Streamlit services.' && sleep infinity"]