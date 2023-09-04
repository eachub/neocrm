FROM {crm-cam-common:master}

USER opuser
COPY --chown=opuser:opuser . /opt/soft/crm-cam-mgr
USER opuser
RUN mkdir /opt/soft/crm-cam-mgr/logs
RUN mkdir /opt/soft/crm-cam-mgr/tasks/logs
RUN mkdir /opt/soft/crm-cam-mgr/stats/logs
RUN mkdir /opt/soft/crm-cam-mgr/target

#CMD ["./run_prod.sh", "non-daemon"]
