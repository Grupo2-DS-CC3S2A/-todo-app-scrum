package pe.edu.uni.firma.common.patterns.creational;

import com.mycompany.digitalsignature.service.RSAKeyGeneratorService;

/** Factory concreta que reutiliza el servicio Java original RSAKeyGeneratorService. */
public class RsaKeyPairFactory implements KeyPairFactory {
    @Override
    public RsaKeyPairMaterial create() {
        RSAKeyGeneratorService generator = new RSAKeyGeneratorService();
        generator.generateKeyPair();
        return new RsaKeyPairMaterial(generator.getRsaPrivateKey(), generator.getRsaPublicKey());
    }
}
