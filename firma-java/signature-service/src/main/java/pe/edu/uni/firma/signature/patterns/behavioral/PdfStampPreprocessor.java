package pe.edu.uni.firma.signature.patterns.behavioral;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.time.Instant;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.springframework.core.annotation.Order;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.signature.dto.CitizenPrivateDto;

/** Strategy concreto: agrega un sello visual al PDF antes de calcular hash y firma. */
@Component
@Order(1)
public class PdfStampPreprocessor implements DocumentPreprocessor {
    @Override
    public boolean supports(String fileName, String contentType) {
        String name = fileName == null ? "" : fileName.toLowerCase();
        String type = contentType == null ? "" : contentType.toLowerCase();
        return name.endsWith(".pdf") || type.contains("pdf");
    }

    @Override
    public PreparedDocument prepare(String fileName, String contentType, byte[] content, CitizenPrivateDto signer) {
        try (PDDocument document = PDDocument.load(content);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            PDPage page = document.getPage(document.getNumberOfPages() - 1);
            PDRectangle box = page.getMediaBox();
            float x = 36;
            float y = Math.max(28, box.getLowerLeftY() + 28);
            float width = 330;
            float height = 45;

            try (PDPageContentStream cs = new PDPageContentStream(document, page, PDPageContentStream.AppendMode.APPEND, true, true)) {
                cs.setStrokingColor(147, 0, 10);
                cs.setNonStrokingColor(255, 246, 246);
                cs.addRect(x, y, width, height);
                cs.fillAndStroke();

                cs.beginText();
                cs.setNonStrokingColor(147, 0, 10);
                cs.setFont(PDType1Font.HELVETICA_BOLD, 9);
                cs.newLineAtOffset(x + 10, y + height - 16);
                cs.showText("Firmado digitalmente por DNI: " + signer.dni());
                cs.endText();

                cs.beginText();
                cs.setNonStrokingColor(60, 40, 40);
                cs.setFont(PDType1Font.HELVETICA, 8);
                cs.newLineAtOffset(x + 10, y + height - 30);
                cs.showText(shortText(signer.apellidosNombres(), 48));
                cs.endText();

                cs.beginText();
                cs.setNonStrokingColor(60, 40, 40);
                cs.setFont(PDType1Font.HELVETICA, 7);
                cs.newLineAtOffset(x + 10, y + height - 40);
                cs.showText("Servicio de Firma Digital UNI - " + Instant.now());
                cs.endText();
            }
            document.save(output);
            return new PreparedDocument(fileName, MediaType.APPLICATION_PDF_VALUE, output.toByteArray(), true);
        } catch (IOException ex) {
            throw new IllegalArgumentException("No se pudo insertar el sello visible en el PDF. Verifique que el archivo PDF no esté corrupto o protegido.", ex);
        }
    }

    private String shortText(String value, int max) {
        if (value == null) return "";
        return value.length() <= max ? value : value.substring(0, max - 3) + "...";
    }
}
