package pe.edu.uni.firma.common.crypto;

import java.security.KeyFactory;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import static pe.edu.uni.fc.cc.common.Constants.RSA_ALGORITHM;

public class KeyMaterialCodec {
    public String encodePrivate(RSAPrivateKey privateKey) {
        return Base64.getEncoder().encodeToString(privateKey.getEncoded());
    }

    public String encodePublic(RSAPublicKey publicKey) {
        return Base64.getEncoder().encodeToString(publicKey.getEncoded());
    }

    public RSAPrivateKey decodePrivate(String privateKeyBase64) {
        try {
            byte[] data = Base64.getDecoder().decode(privateKeyBase64);
            PKCS8EncodedKeySpec spec = new PKCS8EncodedKeySpec(data);
            return (RSAPrivateKey) KeyFactory.getInstance(RSA_ALGORITHM).generatePrivate(spec);
        } catch (Exception ex) {
            throw new IllegalArgumentException("No se pudo reconstruir la llave privada RSA", ex);
        }
    }

    public RSAPublicKey decodePublic(String publicKeyBase64) {
        try {
            byte[] data = Base64.getDecoder().decode(publicKeyBase64);
            X509EncodedKeySpec spec = new X509EncodedKeySpec(data);
            return (RSAPublicKey) KeyFactory.getInstance(RSA_ALGORITHM).generatePublic(spec);
        } catch (Exception ex) {
            throw new IllegalArgumentException("No se pudo reconstruir la llave pública RSA", ex);
        }
    }
}
