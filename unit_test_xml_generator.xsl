<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    version="2.0">
    <xsl:strip-space elements="*" />
    <xsl:output indent="yes"/>
    
    <xsl:template match="text()" />
    
    <xsl:template match="/">
        <root>
            <xsl:apply-templates />
        </root>
    </xsl:template>
    
    <xsl:template match="card">
        <xsl:variable name="word" select="k" />
        <xsl:if test="
            $word = 'а' or
            $word = 'аба' or
            $word = 'ааламдык' or
            $word = 'аарчы' or
            $word = 'якь' or
            $word = 'ячейке' or
            $word = 'хуш' or
            $word = 'локулда'">
            <card>
                <xsl:copy-of select="node()" />
            </card>
        </xsl:if>
    </xsl:template>
    
</xsl:stylesheet>