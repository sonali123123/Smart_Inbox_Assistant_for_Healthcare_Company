package com.smartinbox.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("http://localhost:4200", "http://127.0.0.1:4200")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }

    @Bean
    public RestTemplate restTemplate(AppProperties appProperties) {
        org.springframework.http.client.SimpleClientHttpRequestFactory factory =
                new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(appProperties.getAiService().getConnectTimeoutMs());
        factory.setReadTimeout(appProperties.getAiService().getReadTimeoutMs());
        RestTemplate restTemplate = new RestTemplate(factory);
        restTemplate.getMessageConverters().removeIf(m -> m instanceof org.springframework.http.converter.StringHttpMessageConverter);
        restTemplate.getMessageConverters().add(0, new org.springframework.http.converter.StringHttpMessageConverter(java.nio.charset.StandardCharsets.UTF_8));
        return restTemplate;
    }
}
