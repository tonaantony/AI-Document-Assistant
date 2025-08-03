package com.ai_doc_assistant.ai_service.service;

import java.io.IOException;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import okhttp3.HttpUrl;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

@Service
public class DocumentService {

    private final OkHttpClient client = new OkHttpClient();

    public void processDocument(MultipartFile file) throws IOException {
        PDDocument pdf = PDDocument.load(file.getInputStream());
        PDFTextStripper stripper = new PDFTextStripper();
        String text = stripper.getText(pdf);
        pdf.close();

        // Send to Python for chunking + embedding
        RequestBody body = new MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("text", text)
            .build();

        Request request = new Request.Builder()
            .url("http://localhost:5000/embed")
            .post(body)
            .build();

        client.newCall(request).execute().close();
    }

    public String answerQuestion(String question) {
        HttpUrl.Builder urlBuilder = HttpUrl.parse("http://localhost:5000/query").newBuilder();
        urlBuilder.addQueryParameter("q", question);

        Request request = new Request.Builder()
            .url(urlBuilder.build())
            .get()
            .build();

        try (Response response = client.newCall(request).execute()) {
            return response.body().string();
        } catch (IOException e) {
            return "Error: " + e.getMessage();
        }
    }
}
