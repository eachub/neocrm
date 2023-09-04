FROM {crm-cam-common:master}

USER opuser
COPY --chown=opuser:opuser . /opt/soft/crm-cam-app
USER opuser
RUN mkdir /opt/soft/crm-cam-app/logs
RUN mkdir /opt/soft/crm-cam-app/task/logs

#CMD ["./run_prod.sh", "non-daemon"]
