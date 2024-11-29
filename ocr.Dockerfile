FROM registry.baidubce.com/paddlepaddle/paddle:3.0.0b1

ENV TZ=Asia/Shanghai

ARG OCR_MODEL=PP-OCRv3
ENV OCR_MODEL=${OCR_MODEL}

RUN pip3 install --no-cache-dir --upgrade pip

RUN pip3 install --no-cache-dir --upgrade paddlehub

RUN git clone https://github.com/PaddlePaddle/PaddleOCR.git /PaddleOCR --depth 1

WORKDIR /PaddleOCR

RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install --no-cache-dir protobuf==3.20.3

RUN mkdir -p /PaddleOCR/inference/

ADD https://paddleocr.bj.bcebos.com/${OCR_MODEL}/chinese/ch_${OCR_MODEL}_det_infer.tar /PaddleOCR/inference/
RUN tar xf /PaddleOCR/inference/ch_${OCR_MODEL}_det_infer.tar -C /PaddleOCR/inference/

ADD https://paddleocr.bj.bcebos.com/${OCR_MODEL}/chinese/ch_${OCR_MODEL}_rec_infer.tar /PaddleOCR/inference/
RUN tar xf /PaddleOCR/inference/ch_${OCR_MODEL}_rec_infer.tar -C /PaddleOCR/inference/

ADD https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar /PaddleOCR/inference/
RUN tar xf /PaddleOCR/inference/ch_ppocr_mobile_v2.0_cls_infer.tar -C /PaddleOCR/inference/

RUN sed -i "s/ch_PP-OCRv3_det_infer/ch_${OCR_MODEL}_det_infer/g" deploy/hubserving/ocr_system/params.py
RUN sed -i "s/ch_PP-OCRv3_rec_infer/ch_${OCR_MODEL}_rec_infer/g" deploy/hubserving/ocr_system/params.py
# RUN sed -i 's/ch_ppocr_mobile_v2.0_cls_infer/ch_ppocr_mobile_v2.0_cls_infer/g' deploy/hubserving/ocr_system/params.py

RUN hub install deploy/hubserving/ocr_system/

RUN apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm /PaddleOCR/inference/*.tar

EXPOSE 8866

CMD ["/bin/bash","-c","hub serving start -m ocr_system -p 8866 --use_multiprocess --workers 2"]
