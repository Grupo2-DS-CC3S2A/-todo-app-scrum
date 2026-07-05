package pe.edu.uni.firma.common.patterns.creational;

import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;

/** Patrón Factory Method: contrato para crear pares de llaves. */
public interface KeyPairFactory {
    RsaKeyPairMaterial create();

    record RsaKeyPairMaterial(RSAPrivateKey privateKey, RSAPublicKey publicKey) {}
}
