FROM {neocrm_mtk:master}

USER opuser
COPY --chown=opuser:opuser . /opt/soft/crm-cam-app-adaptation
USER opuser
RUN mkdir /opt/soft/crm-cam-app-adaptation/logs
RUN mkdir /opt/nfs

#CMD ["./run_prod.sh", "non-daemon"]
