package com.mycompany.digitalsignature;

import java.math.BigInteger;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import static pe.edu.uni.fc.cc.common.Constants.RSA_ALGORITHM;
import static pe.edu.uni.fc.cc.common.Constants.RSA_KEY_SIZE_2048;

/** Código académico original conservado: firma RSA directa de un mensaje numérico. */
public class BasicDigitalSignature {
    public static void main(String[] args) {
        System.out.println("Basic Digital Signature!!");
        String originalMessage = "Basic Digital Signature";

        KeyPair kp = null;
        try {
            KeyPairGenerator kpg = KeyPairGenerator.getInstance(RSA_ALGORITHM);
            kpg.initialize(RSA_KEY_SIZE_2048);
            kp = kpg.genKeyPair();
        } catch (NoSuchAlgorithmException ex) {
            System.getLogger(BasicDigitalSignature.class.getName()).log(System.Logger.Level.ERROR, (String) null, ex);
        }

        PrivateKey privateKey = kp.getPrivate();
        PublicKey publicKey = kp.getPublic();
        RSAPrivateKey rsaPrivateKey = (RSAPrivateKey) privateKey;
        RSAPublicKey rsaPublicKey = (RSAPublicKey) publicKey;

        BigInteger d = rsaPrivateKey.getPrivateExponent();
        BigInteger n = rsaPrivateKey.getModulus();
        BigInteger originalBigIntegerMessage = new BigInteger(1, originalMessage.getBytes());
        BigInteger signature = originalBigIntegerMessage.modPow(d, n);

        BigInteger e = rsaPublicKey.getPublicExponent();
        BigInteger recoveredMessage = signature.modPow(e, n);
        boolean verified = recoveredMessage.equals(originalBigIntegerMessage);

        System.out.println("Mensaje original: " + originalMessage);
        System.out.println("Mensaje numérico: " + originalBigIntegerMessage);
        System.out.println("Mensaje firmado: " + signature);
        System.out.println("Mensaje recuperado: " + recoveredMessage);
        System.out.println("Firma válida: " + verified);
    }
}
