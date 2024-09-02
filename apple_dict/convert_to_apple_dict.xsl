<?xml version="1.0"?>
<xsl:stylesheet version="2.0" 
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
                xmlns:udn="http://whatever">
  
  <xsl:output method="xml" indent="yes"/>
  <xsl:strip-space elements="*"/>
  
  <xsl:template match="/root">
    <xsl:text>&#xa;</xsl:text>
    <d:dictionary xmlns="http://www.w3.org/1999/xhtml" xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">
      
      <xsl:for-each select="card">
        <xsl:variable name="word" select="k"/>
        <d:entry>
          <xsl:attribute name="id" select="$word"/>
          <xsl:attribute name="d:title" select="$word"/>
          <d:index>
            <xsl:attribute name="d:value" select="$word"/>
          </d:index>
          <h1><xsl:value-of select="$word"/></h1>
          
              <xsl:choose>
                <xsl:when test="count(meaning) = 0">
                  <xsl:copy-of select="udn:processMeaning(., 0)" />
                </xsl:when>
                <xsl:when test="count(meaning) = 1">
                  <xsl:message terminate="yes">
                    <xsl:value-of select="$word"/>
                  </xsl:message>
                  <xsl:value-of select="error()" />
                  <!-- should never happen, check XML -->
                </xsl:when>
                <xsl:when test="count(meaning) > 1">
                  <xsl:copy-of select="udn:processMeaning(., 0)" />
                  
                  <xsl:for-each select="meaning">
                    <div class="meaningIndex">
                      <xsl:number value="position()" />
                    </div>
                    <xsl:copy-of select="udn:processMeaning(., 0)" />
                  </xsl:for-each>
                </xsl:when>
              </xsl:choose>

        </d:entry>
      </xsl:for-each>
      
    </d:dictionary>
  </xsl:template>
  
  <xsl:function name="udn:processMeaning">
    <xsl:param name="passedMeaning" />
    <xsl:param name="indentationOffset" />
    
    <xsl:for-each select="$passedMeaning/*">
      <xsl:choose>
        <xsl:when test="name() = 'trn'">
          <div class="trn"><xsl:copy-of select="." /></div>
        </xsl:when>
        <xsl:when test="name() = 'blockquote'">
          <div class="blockquote"><xsl:value-of select="."/></div>
        </xsl:when>
      </xsl:choose>
    </xsl:for-each>
  </xsl:function>
  
  <xsl:function name="udn:processRedirectTag">
    <xsl:param name="redirectTag"/>
    <a>
      <xsl:attribute name="href" select="concat('x-dictionary:r:', $redirectTag/@word)"/>
      <xsl:value-of select="$redirectTag/@word"/>
      <xsl:variable name="homonymIndex" select="$redirectTag/@homonym" />
      <xsl:if test="$homonymIndex != ''">
        <xsl:text> </xsl:text>
        <xsl:number value="$homonymIndex" format="I"/>
      </xsl:if>
      <xsl:variable name="meaningIndex" select="$redirectTag/@meaning" />
      <xsl:if test="$meaningIndex != ''">
        <xsl:text> </xsl:text>
        <xsl:number value="$meaningIndex"/>
      </xsl:if>
    </a>
  </xsl:function>
</xsl:stylesheet>