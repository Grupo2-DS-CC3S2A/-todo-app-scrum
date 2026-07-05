package pe.edu.uni.firma.signature.patterns.behavioral;

import java.security.interfaces.RSAPublicKey;
import org.springframework.stereotype.Component;
import pe.edu.uni.firma.common.crypto.OriginalCryptoAdapter;

@Component
public class RsaModularVerificationStrategy implements SignatureVerificationStrategy {
    private final OriginalCryptoAdapter crypto = new OriginalCryptoAdapter();

    @Override
    public boolean verify(byte[] content, String signatureBase64, RSAPublicKey publicKey) {
        return crypto.verifyBase64(content, signatureBase64, publicKey);
    }
}
