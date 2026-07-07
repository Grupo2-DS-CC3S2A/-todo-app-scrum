package com.mycompany.digitalsignature;

import java.math.BigInteger;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import static pe.edu.uni.fc.cc.common.Constants.RSA_ALGORITHM;
import static pe.edu.uni.fc.cc.common.Constants.RSA_KEY_SIZE_2048;
import static pe.edu.uni.fc.cc.common.Constants.SHA_256_ALGORITHM;

/** Código académico original conservado: hash SHA-256 + firma RSA modular. */
public class ProtocolDigitalSignature {
    public static void main(String[] args) {
        System.out.println("Protocol Digital Signature !!!");
        String originalMessage = "Protocol Digital Signature";

        KeyPair kp = null;
        try {
            KeyPairGenerator kpg = KeyPairGenerator.getInstance(RSA_ALGORITHM);
            kpg.initialize(RSA_KEY_SIZE_2048);
            kp = kpg.genKeyPair();
        } catch (NoSuchAlgorithmException ex) {
            System.getLogger(ProtocolDigitalSignature.class.getName()).log(System.Logger.Level.ERROR, (String) null, ex);
        }

        PrivateKey privateKey = kp.getPrivate();
        PublicKey publicKey = kp.getPublic();
        RSAPrivateKey rsaPrivateKey = (RSAPrivateKey) privateKey;
        RSAPublicKey rsaPublicKey = (RSAPublicKey) publicKey;

        BigInteger d = rsaPrivateKey.getPrivateExponent();
        BigInteger n = rsaPrivateKey.getModulus();
        BigInteger originalBigIntegerDigest = null;
        MessageDigest mdMachine = null;
        try {
            mdMachine = MessageDigest.getInstance(SHA_256_ALGORITHM);
            byte[] originalDigest = mdMachine.digest(originalMessage.getBytes());
            originalBigIntegerDigest = new BigInteger(1, originalDigest);
        } catch (NoSuchAlgorithmException ex) {
            System.getLogger(ProtocolDigitalSignature.class.getName()).log(System.Logger.Level.ERROR, (String) null, ex);
        }
        if (originalBigIntegerDigest == null) return;

        BigInteger signature = originalBigIntegerDigest.modPow(d, n);
        BigInteger e = rsaPublicKey.getPublicExponent();
        BigInteger recoveredBigIntegerDigest = signature.modPow(e, n);
        byte[] newDigest = mdMachine.digest(originalMessage.getBytes());
        BigInteger newBigIntegerDigest = new BigInteger(1, newDigest);
        boolean verified = recoveredBigIntegerDigest.equals(newBigIntegerDigest);

        System.out.println("Firma del resumen del mensaje: " + signature);
        System.out.println("Resumen recuperado: " + recoveredBigIntegerDigest.toString(16));
        System.out.println("Resumen calculado: " + newBigIntegerDigest.toString(16));
        System.out.println("Firma válida: " + verified);
    }
}
