package pe.edu.uni.firma.common.crypto;

import com.mycompany.digitalsignature.service.HashingService;
import com.mycompany.digitalsignature.service.ProtocolDigitalSignatureService;
import java.math.BigInteger;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.Base64;

/**
 * Patrón Adapter + Facade criptográfica: adapta los servicios originales basados
 * en BigInteger.modPow a operaciones de alto nivel sobre bytes de archivo.
 */
public class OriginalCryptoAdapter {
    private final HashingService hashingService = new HashingService();
    private final ProtocolDigitalSignatureService signatureService = new ProtocolDigitalSignatureService();

    public String sha256Hex(byte[] content) {
        return hashingService.calculateHashHex(content);
    }

    public BigInteger sha256BigInteger(byte[] content) {
        return hashingService.calculateHash(content);
    }

    public String signToBase64(byte[] content, RSAPrivateKey privateKey) {
        BigInteger hash = sha256BigInteger(content);
        BigInteger signature = signatureService.signDigest(hash, privateKey);
        return Base64.getEncoder().encodeToString(signature.toByteArray());
    }

    public boolean verifyBase64(byte[] content, String signatureBase64, RSAPublicKey publicKey) {
        BigInteger signature = new BigInteger(1, Base64.getDecoder().decode(signatureBase64));
        BigInteger recovered = signatureService.recoverDigest(signature, publicKey);
        BigInteger calculated = sha256BigInteger(content);
        return signatureService.verify(recovered, calculated);
    }
}
