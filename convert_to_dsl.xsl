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
    <xsl:param name="ignoreMetadata" />
    
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
        <xsl:when test="name() = 'metadata'">
          <xsl:if test="$ignoreMetadata != 'true'">
            <xsl:value-of select="foo:processMetadata(., $indentationOffset)"/>
          </xsl:if>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text> </xsl:text>
          <xsl:value-of select="if ($indentationOffset = 0) then '' else ' [m1]'"/>
          <xsl:copy-of select="foo:processOneLineTag(.)" />
          <xsl:value-of select="if ($indentationOffset = 0) then '' else ' [/m]'"/>
          <xsl:text>&#xa;</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each>
  </xsl:function>
  
  <xsl:function name="foo:wrapMetadataInIndentation">
    <xsl:param name="inputText"/>
    <xsl:param name="indentationOffset" />
    <xsl:value-of select="if ($indentationOffset = 0) then ' ' else ' [m1]'"/>
    <xsl:value-of select="$inputText" />
    <xsl:value-of select="if ($indentationOffset = 0) then '&#xa;' else '[/m]&#xa;'"/>
  </xsl:function>
  
  <xsl:function name="foo:processMetadata">
    <xsl:param name="node"/>
    <xsl:param name="indentationOffset" />
    
    <xsl:choose>
      <xsl:when test="$node/@correctForm">
        <xsl:value-of select="if ($indentationOffset = 0) then ' ' else ' [m1]'"/>
        <xsl:text>(неправ. вместо [ref]</xsl:text>
        <xsl:value-of select="$node/@correctForm"/>
        <xsl:text>[/ref])</xsl:text>
        <xsl:value-of select="if ($indentationOffset = 0) then '&#xa;' else '[/m]&#xa;'"/>
      </xsl:when>
    </xsl:choose>
    
    <xsl:variable name="partOfSpeech" select="$node/@part" />
    <xsl:if test="$partOfSpeech != ''">
      <xsl:if test="$partOfSpeech = 'cnjcoo'">
        <xsl:value-of select="foo:wrapMetadataInIndentation('[p]союз[/p]', $indentationOffset)"/>
      </xsl:if>
      <xsl:if test="$partOfSpeech = 'n'">
        <xsl:value-of select="foo:wrapMetadataInIndentation('[p]сущ.[/p]', $indentationOffset)"/>
      </xsl:if>
      <xsl:if test="$partOfSpeech = 'v'">
        <xsl:value-of select="foo:wrapMetadataInIndentation('[p]гл.[/p]', $indentationOffset)"/>
      </xsl:if>
      <xsl:if test="$partOfSpeech = 'adj'">
        <xsl:value-of select="foo:wrapMetadataInIndentation('[p]прил.[/p]', $indentationOffset)"/>
      </xsl:if>
    </xsl:if>
    
    <xsl:choose>
      <xsl:when test="$node/@origin">
        <xsl:choose>
          <xsl:when test="$node/@origin = 'ru'">
            <xsl:value-of select="foo:wrapMetadataInIndentation('[p]р.[/p]', $indentationOffset)"/>
          </xsl:when>
          <xsl:when test="$node/@origin = 'ar'">
            <xsl:value-of select="foo:wrapMetadataInIndentation('[p]ар.[/p]', $indentationOffset)"/>
          </xsl:when>
        </xsl:choose>
      </xsl:when>
    </xsl:choose>
    
    <xsl:if test="$node/@obsolete">
      <xsl:value-of select="foo:wrapMetadataInIndentation('[p]уст.[/p]', $indentationOffset)"/>
    </xsl:if>
    <xsl:if test="$node/@southern">
      <xsl:value-of select="foo:wrapMetadataInIndentation('[p]южн.[/p]', $indentationOffset)"/>
    </xsl:if>
    <xsl:if test="$node/@northern">
      <xsl:value-of select="foo:wrapMetadataInIndentation('[p]сев.[/p]', $indentationOffset)"/>
    </xsl:if>
    <xsl:if test="$node/@rarely">
      <xsl:value-of select="foo:wrapMetadataInIndentation('[p]редко[/p]', $indentationOffset)"/>
    </xsl:if>
    <xsl:if test="$node/@physics">
      <xsl:value-of select="foo:wrapMetadataInIndentation('[p]физ.[/p]', $indentationOffset)"/>
    </xsl:if>
    <xsl:if test="$node/@technics">
      <xsl:value-of select="foo:wrapMetadataInIndentation('[p]тех.[/p]', $indentationOffset)"/>
    </xsl:if>
  </xsl:function>
  
  <xsl:function name="foo:processOneLineTag">
    <xsl:param name="oneLineTag"/>
    
    <xsl:if test="name($oneLineTag) = 'analog'">
      <xsl:text>см. [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'sameas'">
      <xsl:text>то же, что [ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'actionNoun'">
      <xsl:text>и.д. от[ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'pass'">
      <xsl:text>страд. от[ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'refv'">
      <xsl:text>возвр. от[ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'caus'">
      <xsl:text>понуд. от[ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'recv'">
      <xsl:text>взаимн. от[ref]</xsl:text>
      <xsl:value-of select="foo:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'p'">
      <xsl:text>[p]</xsl:text>
      <xsl:value-of select="$oneLineTag"/>
      <xsl:text>[/p]</xsl:text>
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
              <xsl:copy-of select="foo:processMeaning(., 0, 'false')" />
            </xsl:when>
            <xsl:when test="count(meaning) = 1">
              <xsl:value-of select="error()" />
              <!-- should never happen, check XML -->
            </xsl:when>
            <xsl:when test="count(meaning) > 1">
              <xsl:for-each select="meaning">
                <xsl:text> </xsl:text>
                <xsl:number value="position()" />
                <xsl:text>.[/m]&#xa;</xsl:text>
                <xsl:copy-of select="foo:processMeaning(., 0, 'false')" />
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
            
            <xsl:if test="metadata">
              <xsl:value-of select="foo:processMetadata(metadata, 0)"/>
            </xsl:if>
            
            <xsl:choose>
              <xsl:when test="count(meaning) = 0">
                <xsl:copy-of select="foo:processMeaning(., 0, 'true')" />
              </xsl:when>
              <xsl:when test="count(meaning) = 1">
                <xsl:value-of select="error()" />
                <!-- should never happen, check XML -->
              </xsl:when>
              <xsl:when test="count(meaning) > 1">
                <xsl:for-each select="meaning">
                  <xsl:text> [m1]</xsl:text>
                  <xsl:number value="position()" />
                  <xsl:text>.[/m]&#xa;</xsl:text>
                  
                  <xsl:copy-of select="foo:processMeaning(., 1, 'false')" />
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