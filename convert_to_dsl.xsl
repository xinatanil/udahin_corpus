<?xml version="1.0"?>
<xsl:stylesheet version="2.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:foo="http://whatever">
  <xsl:character-map name="escape-square-brackets">
    <xsl:output-character character="[" string="\["/>
    <xsl:output-character character="]" string="\]"/>
  </xsl:character-map>
  
  <xsl:output method="xml" encoding="utf-16le" byte-order-mark="yes"/>
  <xsl:strip-space elements="*"/>
  
  <xsl:function name="foo:processRedirectTag">
    <xsl:param name="redirectTag"/>
    <xsl:value-of select="$redirectTag/@word"/>
    <xsl:text>[/ref] </xsl:text>
    <xsl:variable name="refIndex" select="$redirectTag/@index" />
    <xsl:number value="$refIndex" format="I"/>
  </xsl:function>
  
  <xsl:function name="foo:processMeaning">
    <xsl:param name="passedMeaning" />
    <xsl:param name="indentationOffset" />
    
    <xsl:for-each select="$passedMeaning/*">
      <xsl:choose>
        <xsl:when test="name() = 'k'">
        </xsl:when>
        <xsl:when test="name() = 'trn'">
          <xsl:value-of select="if ($indentationOffset = 0) then ' [m1]' else ' [m2]'"/>
          <xsl:copy-of select="foo:processOneLineTag(.)" />
          <xsl:text>[/m]&#xa;</xsl:text>
        </xsl:when>
        <xsl:when test="name() = 'ex'">
          <xsl:value-of select="if ($indentationOffset = 0) then ' [m1][*]' else ' [m2][*]'"/>
          <xsl:copy-of select="foo:processOneLineTag(.)" />
          <xsl:text>[/*][/m]&#xa;</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:variable name="result" select="foo:processOneLineTag(.)" />
          <xsl:if test="$result != ''">
            <xsl:text> </xsl:text>
            <xsl:value-of select="if ($indentationOffset = 0) then '' else '[m1]'"/>
            <xsl:copy-of select="$result" />
            <xsl:value-of select="if ($indentationOffset = 0) then '' else '[/m]'"/>
            <xsl:text>&#xa;</xsl:text>
          </xsl:if>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each>
  </xsl:function>
  
  <xsl:function name="foo:processOneLineTag">
    <xsl:param name="oneLineTag"/>
    
    <xsl:if test="name($oneLineTag) = 'look'">
      <xsl:text>см. [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'sameas'">
      <xsl:text>то же, что [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'actionNoun'">
      <xsl:text>и.д. от [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'pass'">
      <xsl:text>страд. от [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'refv'">
      <xsl:text>возвр. от [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'caus'">
      <xsl:text>понуд. от [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'recv'">
      <xsl:text>взаимн. от [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'p'
      or name($oneLineTag) = 'pos'
      or name($oneLineTag) = 'origin'
      or name($oneLineTag) = 'meta'">
      <xsl:text>[p]</xsl:text>
      <xsl:value-of select="$oneLineTag"/>
      <xsl:text>[/p]</xsl:text>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'incorrectInsteadOf'">
      <xsl:text>(неправ. вместо [ref]</xsl:text>
      <xsl:value-of select="$oneLineTag"/>
      <xsl:text>[/ref])</xsl:text>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'incorrect'">
      <xsl:value-of select="$oneLineTag"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'collocation'">
      <xsl:value-of select="$oneLineTag"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'trn'">
      <xsl:copy-of select="$oneLineTag"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'transcription'">
      <xsl:text>\[</xsl:text>
      <xsl:value-of select="$oneLineTag"/>
      <xsl:text>\]</xsl:text>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'ex'">
      <xsl:text>[ex]</xsl:text>
      <xsl:copy-of select="$oneLineTag/source/node()" />
      <xsl:text> – </xsl:text>
      <xsl:copy-of select="$oneLineTag/target/node()" />
      <xsl:text>[/ex]</xsl:text>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'blockquote'">
      <xsl:value-of select="$oneLineTag"/>
    </xsl:if>
  </xsl:function>
  
  
  <xsl:template match="/root">
    <xsl:text>&#xa;</xsl:text>
    <xsl:text>#NAME "Кыргызско-русский словарь"</xsl:text>
    <xsl:text>&#xa;</xsl:text>
    <xsl:text>#INDEX_LANGUAGE "Russian"</xsl:text>
    <xsl:text>&#xa;</xsl:text>
    <xsl:text>#CONTENTS_LANGUAGE "Russian"</xsl:text>
    <xsl:text>&#xa;</xsl:text>
    <xsl:text>&#xa;</xsl:text>
    
    <xsl:for-each select="card">
      <xsl:value-of select="k"/>
      <xsl:text>&#xa;</xsl:text>
      
      <xsl:variable name="homonymsCount" select="count(homonym)" />
      <xsl:choose>
        <xsl:when test="$homonymsCount = 0">
          <xsl:choose>
            <xsl:when test="count(meaning) = 0">
              <xsl:copy-of select="foo:processMeaning(., 0)" />
            </xsl:when>
            <xsl:when test="count(meaning) = 1">
              <xsl:value-of select="error()" />
              <!-- should never happen, check XML -->
            </xsl:when>
            <xsl:when test="count(meaning) > 1">
              <xsl:copy-of select="foo:processMeaning(., 0)" />
              
              <xsl:for-each select="meaning">
                <xsl:text> </xsl:text>
                <xsl:number value="position()" />
                <xsl:text>.&#xa;</xsl:text>
                <xsl:copy-of select="foo:processMeaning(., 0)" />
              </xsl:for-each>
            </xsl:when>
          </xsl:choose>
        </xsl:when>
        <xsl:when test="$homonymsCount = 1">
          <xsl:value-of select="error()" />
          <!-- should never happen, check XML -->
        </xsl:when>
        <xsl:when test="$homonymsCount > 1">
          <xsl:for-each select="homonym">
            <xsl:text> </xsl:text>
            <xsl:number value="position()" format="I"/>
            <xsl:text>&#xa;</xsl:text>
            
            <xsl:choose>
              <xsl:when test="count(meaning) = 0">
                <xsl:copy-of select="foo:processMeaning(., 0)" />
              </xsl:when>
              <xsl:when test="count(meaning) = 1">
                <xsl:value-of select="error()" />
                <!-- should never happen, check XML -->
              </xsl:when>
              <xsl:when test="count(meaning) > 1">
                <xsl:copy-of select="foo:processMeaning(., 0)" />
                
                <xsl:for-each select="meaning">
                  <xsl:text> [m1]</xsl:text>
                  <xsl:number value="position()" />
                  <xsl:text>.[/m]&#xa;</xsl:text>
                  <xsl:copy-of select="foo:processMeaning(., 1)" />
                </xsl:for-each>
              </xsl:when>
            </xsl:choose>
            
          </xsl:for-each>
          
        </xsl:when>
      </xsl:choose>
      
      <xsl:text>&#xa;</xsl:text> <!-- separator line between card -->
      
    </xsl:for-each>
    
  </xsl:template>
</xsl:stylesheet>