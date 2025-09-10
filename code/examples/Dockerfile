# syntax=docker/dockerfile:1

# This Dockerfile shows how you can both build and run a container with
# an MQ Python program.
#
# It can cope with both platforms where a Redistributable Client is available, and platforms
# where it is not - copy the .rpm or .deb install images for such platforms into the MQINST
# subdirectory of this repository first. The UBI base image used here is rpm-based.

ARG BASE_IMAGE=registry.access.redhat.com/ubi8/python-312
FROM $BASE_IMAGE

ENV VRMF=9.4.3.0 \
    genmqpkg_incnls=1 \
    genmqpkg_incsdk=1 \
    genmqpkg_inctls=1

USER 0

# Create directory structure
RUN mkdir -p /opt/mqm \
    && mkdir -p /MQINST \
    && chmod a+rx /opt/mqm

# This is needed for the Redist Client in many situations
RUN mkdir -p /IBM/MQ/data/errors \
    && mkdir -p /.mqm \
    && chmod -R 777 /IBM \
    && chmod -R 777 /.mqm

WORKDIR /opt/app-root/src

# Install MQ client and SDK.
#
# For platforms with a Redistributable client, we can use curl to pull it in and unpack it.
#
# For most other platforms, you can have deb or rpm files available in MQINST directory, under the current directory,
# and we then copy them into the container image. Use dpkg or rpm to install from them; these have to be
# done in the right order.
#
# The rpm version of the install packages have a different VRMF format: instead of "9.1.2.3", they have "9.1.2-3" in
# the filenames. So we need to convert using sed. Note that the rpm signing information will not be in the container
# unless you modify this Dockerfile.
#
# The Linux ARM64 image is a full-function server package that is directly unpacked.
# We only need a subset of the files so strip the unneeded filesets. The download of the image could
# be automated via curl in the same way as the Linux/amd64 download, but it's a much bigger image and
# has a different license. So I'm not going to do that for now.
#
# If additional Redistributable Client platforms appear, then this block can be altered, including the MQARCH setting.
#
# The copy of the README is so that at least one file always gets copied, even if you don't have the rpm/deb files locally.
# Using a wildcard in the directory name also helps to ensure that this part of the build always succeeds.
COPY README.md MQINST*/*deb MQINST*/*rpm MQINST*/*tar.gz /MQINST/

# These are values always set by the "docker build" process
ARG TARGETARCH TARGETOS
RUN echo "Target arch is $TARGETARCH; os is $TARGETOS"
# Might need to refer to TARGET* vars a few times in this block, so define something shorter.
ARG RDURL_ARG="https://public.dhe.ibm.com/ibmdl/export/pub/software/websphere/messaging/mqdev/redist"
RUN T="$TARGETOS/$TARGETARCH"; \
      if [ "$T" = "linux/amd64" ]; \
      then \
        MQARCH=X64;\
        RDURL=${RDURL_ARG};\
        RDTAR="IBM-MQC-Redist-Linux${MQARCH}.tar.gz"; \
        cd /opt/mqm \
        && curl -LO "$RDURL/$VRMF-$RDTAR" \
        && tar -zxf ./*.tar.gz \
        && rm -f ./*.tar.gz \
        && bin/genmqpkg.sh -b /opt/mqm;\
      elif [ "$T" = "linux/arm64" ] ;\
      then \
        cd /MQINST; \
        c=`ls *$VRMF*.tar.gz 2>/dev/null| wc -l`; if [ $c -ne 1 ]; then echo "MQ installation file does not exist in MQINST subdirectory";exit 1;fi; \
        cd /opt/mqm \
        && tar -zxf /MQINST/*.tar.gz \
        && export genmqpkg_incserver=0 \
        && bin/genmqpkg.sh -b /opt/mqm;\
      elif [ "$T" = "linux/ppc64le" -o "$T" = "linux/s390x" ];\
      then \
        cd /MQINST; \
        RHVRMF=`echo "$VRMF" | sed "s/\(.*\)\./\1-/"`;\
        cdeb=`ls ibmmq-*$VRMF*.deb 2>/dev/null| wc -l`; \
        crpm=`ls MQSeries*$RHVRMF*.rpm 2>/dev/null| grep "$VRMF" | wc -l`; \
        if [ $cdeb -ge 4 ]; \
        then \
          for f in ibmmq-runtime_$VRMF*.deb ibmmq-gskit_$VRMF*.deb ibmmq-client_$VRMF*.deb ibmmq-sdk_$VRMF*.deb;\
          do dpkg -i $f;\
          done; \
        elif [ $crpm -ge 4 ]; \
        then \
          rpm --noverify -i MQSeriesRuntime-$RHVRMF*.rpm MQSeriesGSKit-$RHVRMF*.rpm MQSeriesClient-$RHVRMF*.rpm MQSeriesSDK-$RHVRMF*.rpm;\
          if [ $? -ne 0 ]; then exit 1;fi;\
        else \
          echo "MQ installation files do not exist in MQINST subdirectory";\
          exit 1;\
        fi;\
      else   \
        echo "Unsupported platform $T";\
        exit 1;\
      fi

# Make sure the MQ client libraries can be found at runtime
ENV LD_LIBRARY_PATH=/opt/mqm/lib64

# User 1001 is the default application user in this base container image
USER 1001

# Install the MQ Python library. This will build against the installed SDK
# RUN pip install --verbose --config-settings=--build-option=server ibmmq
RUN pip install ibmmq

# Copy a sample program into the container
COPY connect_simple.py .      

# And set things up so that sample is executed automatically when the container starts
 CMD ["python", "connect_simple.py"]
# CMD ["bash"]
