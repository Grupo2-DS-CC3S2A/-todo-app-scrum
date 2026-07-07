package pe.edu.uni.firma.signature.patterns.behavioral;

import java.security.interfaces.RSAPublicKey;

/** Patrón Strategy: diferentes formas de verificar una firma podrían implementarse aquí. */
public interface SignatureVerificationStrategy {
    boolean verify(byte[] content, String signatureBase64, RSAPublicKey publicKey);
}
