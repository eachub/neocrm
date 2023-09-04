FROM {neocrm_mtk:master}

USER opuser
COPY --chown=opuser:opuser . /opt/soft/crm-mgr-adaptation

USER opuser
RUN mkdir /opt/soft/crm-mgr-adaptation/logs
RUN mkdir /opt/soft/crm-mgr-adaptation/tasks/logs

#CMD ["./run_prod.sh", "non-daemon"]
