FROM {neocrm-mtk:master}

USER opuser
RUN pip3 install openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip3 install xlwt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY --chown=opuser:opuser . /opt/soft/crm-backend/crm-common
WORKDIR /opt/soft/crm-backend/crm-common