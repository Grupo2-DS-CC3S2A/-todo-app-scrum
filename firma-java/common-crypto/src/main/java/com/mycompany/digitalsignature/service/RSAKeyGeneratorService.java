package com.mycompany.digitalsignature.service;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import static pe.edu.uni.fc.cc.common.Constants.RSA_ALGORITHM;
import static pe.edu.uni.fc.cc.common.Constants.RSA_KEY_SIZE_2048;

/** Servicio original de generación de llaves RSA 2048. */
public class RSAKeyGeneratorService {
    private RSAPrivateKey rsaPrivateKey;
    private RSAPublicKey rsaPublicKey;

    public RSAPrivateKey getRsaPrivateKey() { return rsaPrivateKey; }
    public RSAPublicKey getRsaPublicKey() { return rsaPublicKey; }

    public void generateKeyPair() {
        try {
            KeyPairGenerator kpg = KeyPairGenerator.getInstance(RSA_ALGORITHM);
            kpg.initialize(RSA_KEY_SIZE_2048);
            KeyPair kp = kpg.generateKeyPair();
            this.rsaPrivateKey = (RSAPrivateKey) kp.getPrivate();
            this.rsaPublicKey = (RSAPublicKey) kp.getPublic();
        } catch (NoSuchAlgorithmException ex) {
            System.getLogger(RSAKeyGeneratorService.class.getName()).log(System.Logger.Level.ERROR, (String) null, ex);
        }
    }
}
