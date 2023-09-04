FROM {crm-common:master}

USER opuser
COPY --chown=opuser:opuser . /opt/soft/crm-backend/crm-app
USER opuser
RUN mkdir /opt/soft/crm-backend/crm-app/logs
RUN mkdir /opt/soft/crm-backend/crm-app/tasks/logs

