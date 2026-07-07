package pe.edu.uni.firma.signature.patterns.behavioral;

import pe.edu.uni.firma.signature.dto.CitizenPrivateDto;

/** Patrón Strategy: cada tipo de documento puede preparar el contenido antes de firmarlo. */
public interface DocumentPreprocessor {
    boolean supports(String fileName, String contentType);
    PreparedDocument prepare(String fileName, String contentType, byte[] content, CitizenPrivateDto signer);
}
