FROM python
EXPOSE 5000

RUN pip install flask pillow

ADD frontend.py ./
ADD spa.html ./

ENTRYPOINT python frontend.py