FROM {crm-common:master}

USER opuser
COPY --chown=opuser:opuser . /opt/soft/crm-backend/crm-mgr

USER opuser
RUN mkdir /opt/soft/crm-backend/crm-mgr/logs
RUN mkdir /opt/soft/crm-backend/crm-mgr/tasks/logs
RUN mkdir /opt/soft/crm-backend/crm-mgr/stats/logs
RUN mkdir /opt/soft/crm-backend/crm-mgr/target

#CMD ["./run_prod.sh", "non-daemon"]