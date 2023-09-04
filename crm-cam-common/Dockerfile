FROM {neocrm_mtk:master}

USER opuser
COPY --chown=opuser:opuser . /opt/soft/crm-cam-common
RUN pip3 install numpy==1.22.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /opt/soft/crm-cam-common
