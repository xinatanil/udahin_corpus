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
          
          <xsl:variable name="homonymsCount" select="count(homonym)" />
          <xsl:choose>
            <xsl:when test="$homonymsCount = 0">
              <xsl:choose>
                <xsl:when test="count(meaning) = 0">
                  <xsl:copy-of select="udn:processMeaning(., 0)" />
                </xsl:when>
                <xsl:when test="count(meaning) = 1">
                  <xsl:value-of select="error()" />
                  <!-- should never happen, check XML -->
                </xsl:when>
                <xsl:when test="count(meaning) > 1">
                  <xsl:copy-of select="udn:processMeaning(., 0)" />
                  
                  <xsl:for-each select="meaning">
                    <xsl:number value="position()" />
                    <br/>
                    <xsl:copy-of select="udn:processMeaning(., 0)" />
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
                <xsl:number value="position()" format="I"/>
                <br/>
                
                <xsl:choose>
                  <xsl:when test="count(meaning) = 0">
                    <xsl:copy-of select="udn:processMeaning(., 0)" />
                  </xsl:when>
                  <xsl:when test="count(meaning) = 1">
                    <xsl:value-of select="error()" />
                    <!-- should never happen, check XML -->
                  </xsl:when>
                  <xsl:when test="count(meaning) > 1">
                    <xsl:copy-of select="udn:processMeaning(., 0)" />
                    
                    <xsl:for-each select="meaning">
                      <xsl:number value="position()" />
                      <br/>
                      <xsl:copy-of select="udn:processMeaning(., 0)" />
                    </xsl:for-each>
                  </xsl:when>
                </xsl:choose>
                
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
        <xsl:when test="name() = 'k'">
          <xsl:if test="name(..) = 'collocation'">
            <div class="headword">
              <xsl:value-of select="." />
            </div>
          </xsl:if>
        </xsl:when>
        <xsl:when test="name() = 'trn'">
          <div class="trn"><xsl:copy-of select="." /></div>
        </xsl:when>
        <xsl:when test="name() = 'ex'">
          <div class="ex">
            <div class="source"><xsl:copy-of select="source/node()"/></div>
            <div class="target"><xsl:copy-of select="target/node()"/></div>
          </div>
        </xsl:when>
        <xsl:when test="name() = 'collocation'">
          <div class="collocation">
            <xsl:copy-of select="udn:processMeaning(., $indentationOffset)" />
          </div>
        </xsl:when>
        <xsl:otherwise>
          <xsl:variable name="result" select="udn:processOneLineTag(.)" />
          <xsl:if test="$result != ''">
            <xsl:copy-of select="$result" />
          </xsl:if>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each>
  </xsl:function>
  
  <xsl:function name="udn:processOneLineTag">
    <xsl:param name="oneLineTag"/>
    
    <xsl:if test="name($oneLineTag) = 'look'">
      <xsl:text>см. </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'sameas'">
      <xsl:text>то же, что </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'actionNoun'">
      <xsl:text>и.д. от </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'pass'">
      <xsl:text>страд. от </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'refv'">
      <xsl:text>возвр. от </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'caus'">
      <xsl:text>понуд. от </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'recv'">
      <xsl:text>взаимн. от </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'like'">
      <xsl:text>уподоб. от </xsl:text>
      <xsl:copy-of select="udn:processRedirectTag($oneLineTag)"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'p'">
      <xsl:copy-of select="$oneLineTag"/>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'origin'">
      <div class="origin">
        <xsl:copy-of select="$oneLineTag/node()"/>
      </div>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'pos'">
      <div class="pos">
        <xsl:copy-of select="$oneLineTag/node()"/>
      </div>
    </xsl:if>    
    <xsl:if test="name($oneLineTag) = 'meta'">
      <div class="meta">
        <xsl:copy-of select="$oneLineTag/node()"/>
      </div>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'incorrectInsteadOf'">
      <xsl:text>(неправ. вместо [ref]</xsl:text>
      <xsl:value-of select="$oneLineTag"/>
      <xsl:text>[/ref])</xsl:text>
    </xsl:if>
    <xsl:if test="name($oneLineTag) = 'incorrect'">
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
    <xsl:if test="name($oneLineTag) = 'blockquote'">
      <xsl:value-of select="$oneLineTag"/>
    </xsl:if>
  </xsl:function>
  
  <xsl:function name="udn:processRedirectTag">
    <xsl:param name="redirectTag"/>
    <a>
      <xsl:attribute name="href" select="concat('x-dictionary:r:', $redirectTag/@word)"/>
      <xsl:value-of select="$redirectTag/@word"/>
      <xsl:variable name="homonymIndex" select="$redirectTag/@index" />
      <xsl:if test="$homonymIndex != ''">
        <xsl:text> </xsl:text>
        <xsl:number value="$homonymIndex" format="I"/>
      </xsl:if>
      <xsl:variable name="meaningIndex" select="$redirectTag/@subindex" />
      <xsl:if test="$meaningIndex != ''">
        <xsl:text> </xsl:text>
        <xsl:number value="$meaningIndex"/>
      </xsl:if>
    </a>
  </xsl:function>
</xsl:stylesheet>