from openai import OpenAI
import sys

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

client = OpenAI()

prompt = """
You are a lexicographer.
You are working on improving an existing Kyrgyz-Russian dictionary by Konstantin Yudakhin.
The dictionary has been scanned and converted into a giant XML file, and while it’s readable, it does contain a small amount of scanning errors.
You will receive <card>
Here’s the description of the XML structure:
Each entry is enclosed in a <card> tag.
Inside every <card>, the very first tag you’ll see is a required <k> tag, which contains a header word.
You might also encounter <meta> and <origin> tags, they contain conditional abbreviations.
You might also encounter <meaning> tags which contain different meanings of the header word (in case there’s more than one).
The rest of the text will come in <blockquote> tags.

So, an example of an entry would look like this:
    <card>
        <k>ада</k>
        <origin>ар.</origin>
        <meaning>
            <blockquote>1. конец, окончание, завершение; иссякание;</blockquote>
            <blockquote>ада бол- закончиться, кончиться; иссякнуть;</blockquote>
            <blockquote>ада бол! пропади ты!;</blockquote>
            <blockquote>ада кыл- кончить, закончить, завершить; довести до иссякания;</blockquote>
            <blockquote>малдын барын түгөтүп, ада кылды жанбакты стих. извёл и прикончил весь скот, бездельник;</blockquote>
        </meaning>
        <meaning>
            <blockquote>2. выполнение, исполнение;</blockquote>
            <blockquote>ада болсо если исполнится (свершится).</blockquote>
        </meaning>
    </card>

Your job is to detect whether contents of a <blockquote> tag is a usage example of the header word.

Hints to help you identify a usage example:
1. Content begins with text in Kyrgyz.
2. Content ends with text in Russian.
3. There may be conditional abbreviations in the middle of the line, such as “миф.”, “стих.”, “южн.” and others
4. Most likely, content will contain a word very similar to the header word.

If you’re sure the line contains a usage example, then:
1. Replace the <blockquote> tag with <ex>.
2. Enclose the Kyrgyz text in the <source> tag.
3. Enclose the Russian text in the <target> tag.
4. Place the conditional abbreviations (such as “миф.”, “стих.”, “южн.” and others) inside the <target> tag along with the Russian text.

So, an ideally marked version of an example above would look like this:

    <card>
        <k>ада</k>
        <origin>ар.</origin>
        <meaning>
            <trn>1. конец, окончание, завершение; иссякание;</trn>
            <ex>
                <source>ада бол-</source>
                <target>закончиться, кончиться; иссякнуть;</target>
            </ex>
            <ex>
                <source>ада бол!</source>
                <target>пропади ты!;</target>
            </ex>
            <ex>
                <source>ада кыл-</source>
                <target>кончить, закончить, завершить; довести до иссякания;</target>
            </ex>
            <ex>
                <source>малдын барын түгөтүп, ада кылды жанбакты</source> 
                <target>стих. извёл и прикончил весь скот, бездельник;</target>
            </ex>
        </meaning>
        <meaning>
            <trn>2. выполнение, исполнение;</trn>
            <ex>
                <source>ада болсо</source>
                <target>если исполнится (свершится).</target>
            </ex>
        </meaning>
    </card>
    
Your response must not contain markdown, return XML only

Below are more before/after examples.

<k>күч</k> Before:

	<card>
		<k>күч</k>
		<meaning>
			<blockquote>1. сила;</blockquote>
			<blockquote>күч атасын тааныбайт погов. сила (и) отца своего не признаёт;</blockquote>
			<blockquote>киши күчү воен. живая сила;</blockquote>
			<blockquote>киши күчүн жоготуу уничтожение живой силы;</blockquote>
			<blockquote>Советтер Союзунун күч-кубаттуулугу мощь Советского Союза;</blockquote>
			<blockquote>аттын күчү</blockquote>
			<blockquote>1) сила лошади;</blockquote>
			<blockquote>2) тех. лошадиная сила;</blockquote>
			<blockquote>күч аракетибизди аябайбыз мы не пожалеем своих сил;</blockquote>
			<blockquote>күчкө кел- или күч ал- усиливаться;</blockquote>
			<blockquote>аяз кырчылдап күчүнө келди мороз трещал и усиливался;</blockquote>
			<blockquote>бороон дагы күч алды буран ещё более усилился;</blockquote>
			<blockquote>күчүнө келип турган кези он в полной силе;</blockquote>
			<blockquote>күч кайтты силы оставили;</blockquote>
			<blockquote>байбичемден күч кайтып, мен өңдөнүп карыган фольк. жену (см. <wordLink word="байбиче"/>) мою силы оставили, подобно мне постарела;</blockquote>
			<blockquote>бала жок, кемпирим экөөбүз эле, эми минтип күч кайтты детей (у нас) нет, мы вдвоём со старухой теперь совсем беспомощны;</blockquote>
		</meaning>
		<meaning>
			<blockquote>2. сильный;</blockquote>
			<blockquote>ууру күч болсо, ээси өлөт погов. если вор силён, (то) погибает хозяин (украденной вещи);</blockquote>
		</meaning>
		<meaning>
			<blockquote>3. лошадь, конь;</blockquote>
			<blockquote>союп берип боругун, эки семиз күч берген, алты чанач сүт берген фольк. зарезал он (для них) двух баранов, дал (им) двух жирных коней, дал шесть бурдюков молока;</blockquote>
			<blockquote>күч ат рабочая лошадь;</blockquote>
			<blockquote>күч мал рабочий скот;</blockquote>
		</meaning>
		<meaning>
			<blockquote>4. ист. рабочий скот, взятый на отработки;</blockquote>
			<blockquote>бир күнү апийимин отошуп бермек болуп, күчүн миндим однажды я взял у него для поездки коня с условием отработать на прополке опийного мака;</blockquote>
			<blockquote>бир аттын күчүн алып берейин я тебе достану лошадь в пользование;</blockquote>
			<blockquote>шаарга барып келейин, атыңын күчүн бере тур я хочу съездить в город, дай мне свою лошадь;</blockquote>
			<blockquote>күч акысы плата за наём верхового животного;</blockquote>
			<blockquote>күчүнө сал- положиться на силу чего-л.;</blockquote>
			<blockquote>булдун күчүнө салып полагаясь на силу денег; используя силу денег;</blockquote>
			<blockquote>күч келтир- или күч кыл-притеснять;</blockquote>
			<blockquote>мээге күч келтирбе не утомляй мозг;</blockquote>
			<blockquote>мээсине күч келтирип, иштей берет он работает, не считаясь с мозговым переутомлением;</blockquote>
			<blockquote>көзүнө күч келтирип, ыйлай берет он всё время плачет, утомляя глаза;</blockquote>
			<blockquote>сен мага күч кылба не притесняй, не приневоливай меня;</blockquote>
			<blockquote>билчелик күчкө калгамын фольк. на меня свалилась слоновая (посильная только слону) тяжесть;</blockquote>
			<blockquote>иштегенин маа күч кылат! как будто он для меня работает! (вот ещё выдумал!);</blockquote>
			<blockquote>иштегениңди мага күч кылба ты для себя работаешь, не вали на меня (я тут ни при чём);</blockquote>
			<blockquote>кара күчкө</blockquote>
			<blockquote>1) напрасно;</blockquote>
			<blockquote>кара күчкө иштей берип, арам тер болдум исполняя ненужную работу, я измучился;</blockquote>
			<blockquote>2) притворно, деланно, неестественно;</blockquote>
			<blockquote>кара күчкө катуу каткырып күлдү он деланно и громко засмеялся;</blockquote>
			<blockquote>кара күчкө бышаң-бышаң ыйлады он притворно плакал;</blockquote>
			<blockquote>жанга күч келсе если к горлу подопрёт (если трудно придётся);</blockquote>
			<blockquote>күч жек- напрягать силы, напрягаться;</blockquote>
			<blockquote>күч күйөө см. <wordLink word="күйөө"/>того- II.</blockquote>
		</meaning>
	</card>
    
<k>күч</k> After:

	<card>
		<k>күч</k>
		<meaning>
			<trn>1. сила;</trn>
			<ex>
				<source>күч атасын тааныбайт</source>
				<target>погов. сила (и) отца своего не признаёт</target>
			</ex>
			<ex>
				<source>киши күчү</source>
				<target>воен. живая сила;</target>
			</ex>
			<ex>
				<source>киши күчүн жоготуу</source>
				<target>уничтожение живой силы;</target>
			</ex>
			<ex>
				<source>Советтер Союзунун күч-кубаттуулугу</source>
				<target>мощь Советского Союза;</target>
			</ex>
			<blockquote>аттын күчү</blockquote>
			<blockquote>1) сила лошади;</blockquote>
			<blockquote>2) тех. лошадиная сила;</blockquote>
			<ex>
				<source>күч аракетибизди аябайбыз</source>
				<target>мы не пожалеем своих сил;</target>
			</ex>
			<ex>
				<source>күчкө кел- или күч ал-</source>
				<target>усиливаться;</target>
			</ex>
			<ex>
				<source>аяз кырчылдап күчүнө келди</source>
				<target>мороз трещал и усиливался;</target>
			</ex>
			<ex>
				<source>бороон дагы күч алды</source>
				<target>буран ещё более усилился;</target>
			</ex>
			<ex>
				<source>күчүнө келип турган кези</source>
				<target>он в полной силе;</target>
			</ex>
			<ex>
				<source>күч кайтты</source>
				<target>силы оставили;</target>
			</ex>
			<ex>
				<source>байбичемден күч кайтып, мен өңдөнүп карыган</source>
				<target>фольк. жену (см. <wordLink word="байбиче"/>) мою силы оставили, подобно мне постарела;</target>
			</ex>
			<ex>
				<source>бала жок, кемпирим экөөбүз эле, эми минтип күч кайтты</source>
				<target>детей (у нас) нет, мы вдвоём со старухой теперь совсем беспомощны;</target>
			</ex>
		</meaning>
		<meaning>
			<trn>2. сильный;</trn>
			<ex>
				<source>ууру күч болсо, ээси өлөт</source>
				<target>погов. если вор силён, (то) погибает хозяин (украденной вещи);</target>
			</ex>
		</meaning>
		<meaning>
			<trn>3. лошадь, конь;</trn>
			<ex>
				<source>союп берип боругун, эки семиз күч берген, алты чанач сүт берген</source>
				<target>фольк. зарезал он (для них) двух баранов, дал (им) двух жирных коней, дал шесть бурдюков молока;</target>
			</ex>
			<ex>
				<source>күч ат</source>
				<target>рабочая лошадь;</target>
			</ex>
			<ex>
				<source>күч мал</source>
				<target>рабочий скот;</target>
			</ex>
		</meaning>
		<meaning>
			<trn>4. ист. рабочий скот, взятый на отработки;</trn>
			<ex>
				<source>бир күнү апийимин отошуп бермек болуп, күчүн миндим</source>
				<target>однажды я взял у него для поездки коня с условием отработать на прополке опийного мака;</target>
			</ex>
			<ex>
				<source>бир аттын күчүн алып берейин</source>
				<target>я тебе достану лошадь в пользование;</target>
			</ex>
			<ex>
				<source>шаарга барып келейин, атыңын күчүн бере тур</source>
				<target>я хочу съездить в город, дай мне свою лошадь;</target>
			</ex>
			<ex>
				<source>күч акысы</source>
				<target>плата за наём верхового животного;</target>
			</ex>
			<ex>
				<source>күчүнө сал-</source>
				<target> положиться на силу чего-л.;</target>
			</ex>
			<ex>
				<source>булдун күчүнө салып</source>
				<target>полагаясь на силу денег; используя силу денег;</target>
			</ex>
			<ex>
				<source>күч келтир- или күч кыл-</source>
				<target>притеснять;</target>
			</ex>
			<ex>
				<source>мээге күч келтирбе</source>
				<target>не утомляй мозг;</target>
			</ex>
			<ex>
				<source>мээсине күч келтирип, иштей берет</source>
				<target>он работает, не считаясь с мозговым переутомлением;</target>
			</ex>
			<ex>
				<source>көзүнө күч келтирип, ыйлай берет</source>
				<target>он всё время плачет, утомляя глаза;</target>
			</ex>
			<ex>
				<source>сен мага күч кылба</source>
				<target>не притесняй, не приневоливай меня;</target>
			</ex>
			<ex>
				<source>билчелик күчкө калгамын</source>
				<target>фольк. на меня свалилась слоновая (посильная только слону) тяжесть;</target>
			</ex>
			<ex>
				<source>иштегенин маа күч кылат!</source>
				<target> как будто он для меня работает! (вот ещё выдумал!);</target>
			</ex>
			<ex>
				<source>иштегениңди мага күч кылба</source>
				<target>ты для себя работаешь, не вали на меня (я тут ни при чём);</target>
			</ex>
			<blockquote>кара күчкө</blockquote>
			<blockquote>1) напрасно;</blockquote>
			<ex>
				<source>кара күчкө иштей берип, арам тер болдум</source>
				<target>исполняя ненужную работу, я измучился;</target>
			</ex>
			<blockquote>2) притворно, деланно, неестественно;</blockquote>
			<ex>
				<source>кара күчкө катуу каткырып күлдү</source>
				<target>он деланно и громко засмеялся;</target>
			</ex>
			<ex>
				<source>кара күчкө бышаң-бышаң ыйлады</source>
				<target>он притворно плакал;</target>
			</ex>
			<ex>
				<source>жанга күч келсе</source>
				<target>если к горлу подопрёт (если трудно придётся);</target>
			</ex>
			<ex>
				<source>күч жек-</source>
				<target>напрягать силы, напрягаться;</target>
			</ex>
			<blockquote>күч күйөө см. <wordLink word="күйөө"/>того- II.</blockquote>
		</meaning>
	</card>
    
<k>ынтымак</k> Before:

	<card>
		<k>ынтымак</k>
		<origin>ар.</origin>
		<meaning>
			<blockquote>1. согласие, единодушие;</blockquote>
			<blockquote>ырыс алды - ынтымак погов. залог счастья - в единении;</blockquote>
			<blockquote>ынтымактары өтө тыгыз они очень дружны;</blockquote>
			<blockquote>ынтымак курулган жерде ырыс өзү келет там, где установилось согласие, счастье само приходит;</blockquote>
			<blockquote>ынтымагың болбосо, ит менен кушка жем болорсуң погов. если у тебя нет согласия (с другими), ты станешь пищей для псов и хищных птиц;</blockquote>
			<blockquote>экөөнүн арасында ынтымагы жок между ними нет согласия; они между собой не ладят;</blockquote>
			<blockquote>экөөнүн ортосунан ынтымак кетти они оба между собой не поладили;</blockquote>
			<blockquote>ынтымак-ырашкер см. <wordLink word="ырашкер"/></blockquote>
		</meaning>
		<meaning>
			<blockquote>2. этн. помощь родственников и друзей убойным скотом, деньгами (гл. обр. на похороны, поминки, на свадьбу);</blockquote>
			<blockquote>ынтымак кош- вносить свой взнос убойным скотом, деньгами;</blockquote>
			<blockquote>ынтымакка колунда барын кошот на помощь каждый даёт то, что может (букв. то, что имеет);</blockquote>
			<blockquote>ынтымак сура- просить материальной помощи (у родственников, друзей);</blockquote>
			<blockquote>эмесе, Саадат бизден сурабаганда, ынтымакты кимден сурасын? а уж если так, то у кого же Саадат может просить помощи, как не у нас?</blockquote>
		</meaning>
		<meaning>
			<blockquote>3. этн. совещание родственников и друзей о размерах помощи убойным скотом, деньгами с каждого;</blockquote>
			<blockquote>ынтымагына барбай койсок, кутулабызбы? а если мы не пойдём на такое совещание, так избавимся (от взносов) ?</blockquote>
		</meaning>
		<meaning>
			<blockquote>4. сев. то же, что <wordLink word="үн"/>элгек (см. <wordLink word="элгек" homonym="I"/>).</blockquote>
		</meaning>
	</card>
    
<k>ынтымак</k> After:

	<card>
		<k>ынтымак</k>
		<origin>ар.</origin>
		<meaning>
			<trn>1. согласие, единодушие;</trn>
			<ex>
				<source>ырыс алды - ынтымак</source>
				<target>погов. залог счастья - в единении;</target>
			</ex>
			<ex>
				<source>ынтымактары өтө тыгыз</source>
				<target>они очень дружны;</target>
			</ex>
			<ex>
				<source>ынтымак курулган жерде ырыс өзү келет</source>
				<target>там, где установилось согласие, счастье само приходит;</target>
			</ex>
			<ex>
				<source>ынтымагың болбосо, ит менен кушка жем болорсуң</source>
				<target>погов. если у тебя нет согласия (с другими), ты станешь пищей для псов и хищных птиц;</target>
			</ex>
			<ex>
				<source>экөөнүн арасында ынтымагы жок</source>
				<target>между ними нет согласия; они между собой не ладят;</target>
			</ex>
			<ex>
				<source>экөөнүн ортосунан ынтымак кетти</source>
				<target>они оба между собой не поладили;</target>
			</ex>
			<blockquote>ынтымак-ырашкер см. <wordLink word="ырашкер"/></blockquote>
		</meaning>
		<meaning>
			<trn>2. этн. помощь родственников и друзей убойным скотом, деньгами (гл. обр. на похороны, поминки, на свадьбу);</trn>
			<ex>
				<source>ынтымак кош-</source>
				<target>вносить свой взнос убойным скотом, деньгами;</target>
			</ex>
			<ex>
				<source>ынтымакка колунда барын кошот</source>
				<target>на помощь каждый даёт то, что может (букв. то, что имеет);</target>
			</ex>
			<ex>
				<source>ынтымак сура-</source>
				<target>просить материальной помощи (у родственников, друзей);</target>
			</ex>
			<ex>
				<source>эмесе, Саадат бизден сурабаганда, ынтымакты кимден сурасын?</source>
				<target>а уж если так, то у кого же Саадат может просить помощи, как не у нас?</target>
			</ex>
		</meaning>
		<meaning>
			<trn>3. этн. совещание родственников и друзей о размерах помощи убойным скотом, деньгами с каждого;</trn>
			<ex>
				<source>ынтымагына барбай койсок, кутулабызбы?</source>
				<target>а если мы не пойдём на такое совещание, так избавимся (от взносов) ?</target>
			</ex>
		</meaning>
		<meaning>
			<blockquote>4. сев. то же, что <wordLink word="үн"/>элгек (см. <wordLink word="элгек" homonym="I"/>).</blockquote>
		</meaning>
	</card>

<k>жөнөкөй</k> Before:

	<card>
		<k>жөнөкөй</k>
		<blockquote>простой, обыкновенный; несложный; безыскусственный; так себе, просто так; без дела; без цели, без причины;</blockquote>
		<blockquote>жөнөкөй чындык простая истина;</blockquote>
		<blockquote>жөнөкөй жүргөн кишиде эмнең бар? какое тебе дело до постороннего человека (который не имеет касательства к делу) ?</blockquote>
		<blockquote>жөнөкөйдө в обычных условиях, в обычное (а не в какое-л. исключительное) время;</blockquote>
		<blockquote>жөнөкөй көз менен көрүүгө болот можно видеть невооружённым глазом.</blockquote>
	</card>
    
<k>жөнөкөй</k> After:

	<card>
		<k>жөнөкөй</k>
		<trn>простой, обыкновенный; несложный; безыскусственный; так себе, просто так; без дела; без цели, без причины;</trn>
		<ex>
			<source>жөнөкөй чындык</source>
			<target>простая истина;</target>
		</ex>
		<ex>
			<source>жөнөкөй жүргөн кишиде эмнең бар?</source>
			<target>какое тебе дело до постороннего человека (который не имеет касательства к делу) ?</target>
		</ex>
		<ex>
			<source>жөнөкөйдө</source>
			<target>в обычных условиях, в обычное (а не в какое-л. исключительное) время;</target>
		</ex>
		<ex>
			<source>жөнөкөй көз менен көрүүгө болот</source>
			<target>можно видеть невооружённым глазом.</target>
		</ex>
	</card>

<k>бактылуулук</k> Before:

	<card>
		<k>бактылуулук</k>
		<blockquote>счастье, счастливая жизнь, счастливая доля; удачливость;</blockquote>
		<blockquote>элдин бактылуулугу счастье народа, счастливая жизнь народа.</blockquote>
	</card>
    
<k>бактылуулук</k> After:

	<card>
		<k>бактылуулук</k>
		<trn>счастье, счастливая жизнь, счастливая доля; удачливость;</trn>
		<ex>
			<source>элдин бактылуулугу</source>
			<target>счастье народа, счастливая жизнь народа.</target>
		</ex>
	</card>
    
<k>үмүт</k> Before:

	<card>
		<k>үмүт</k>
		<origin>ир.</origin>
		<blockquote>надежда;</blockquote>
		<blockquote>үмүт кыл- или үмүт эт- с предшеств исх. п.</blockquote>
		<blockquote>1) надеяться;</blockquote>
		<blockquote>жаман ит жайлоодогу жармадан үмүт кылат погов. дрянной пёс рассчитывает на похлёбку, которая будет на летовке;</blockquote>
		<blockquote>ит ичпес ашынан үмүт кылат погов. пёс рассчитывает и на ту еду, которая ему не положена;</blockquote>
		<blockquote>2) этн. (о кормящей женщине) надеяться на подарок (несбывшаяся надежда на подарок ведёт, по старому поверъю, к груднице);</blockquote>
		<blockquote>көптөн үмүт эткен аздан куру калат погов. погонишься за большим, и малое потеряешь;</blockquote>
		<blockquote>жандан үмүт кыл- желать сохранить свою жизнь;</blockquote>
		<blockquote>"ач" дегенде, ач эшикти, эгер үмүт кылсан жандан стих. если хочешь остаться живым, то открой дверь, когда говорят "открой";</blockquote>
		<blockquote>жаныңардан үмүт кылсаңар, жакындабагыла! если хотите жить, не приближайтесь!;</blockquote>
		<blockquote>...деген үмүт менен в надежде, что...;</blockquote>
		<blockquote>болорболбос үмүт бар тлеет какая-то надежда;</blockquote>
		<blockquote>үмүт үз- потерять надежду;</blockquote>
		<blockquote>үмүт үзгүм келбейт я не хочу терять надежду.</blockquote>
	</card>
    
<k>үмүт</k> After:

	<card>
		<k>үмүт</k>
		<origin>ир.</origin>
		<trn>надежда;</trn>
		<blockquote>үмүт кыл- или үмүт эт- с предшеств исх. п.</blockquote>
		<blockquote>1) надеяться;</blockquote>
		<ex>
			<source>жаман ит жайлоодогу жармадан үмүт кылат</source>
			<target>погов. дрянной пёс рассчитывает на похлёбку, которая будет на летовке;</target>
		</ex>
		<ex>
			<source>ит ичпес ашынан үмүт кылат</source>
			<target>погов. пёс рассчитывает и на ту еду, которая ему не положена;</target>
		</ex>
		<blockquote>2) этн. (о кормящей женщине) надеяться на подарок (несбывшаяся надежда на подарок ведёт, по старому поверъю, к груднице);</blockquote>
		<ex>
			<source>көптөн үмүт эткен аздан куру калат</source>
			<target>погов. погонишься за большим, и малое потеряешь;</target>
		</ex>
		<ex>
			<source>жандан үмүт кыл-</source>
			<target>желать сохранить свою жизнь;</target>
		</ex>
		<ex>
			<source>"ач" дегенде, ач эшикти, эгер үмүт кылсан жандан</source>
			<target>стих. если хочешь остаться живым, то открой дверь, когда говорят "открой";</target>
		</ex>
		<ex>
			<source>жаныңардан үмүт кылсаңар, жакындабагыла!</source>
			<target>если хотите жить, не приближайтесь!;</target>
		</ex>
		<ex>
			<source>...деген үмүт менен</source>
			<target>в надежде, что...;</target>
		</ex>
		<ex>
			<source>болорболбос үмүт бар</source>
			<target>тлеет какая-то надежда;</target>
		</ex>
		<ex>
			<source>үмүт үз-</source>
			<target>потерять надежду;</target>
		</ex>
		<ex>
			<source>үмүт үзгүм келбейт</source>
			<target>я не хочу терять надежду.</target>
		</ex>
	</card>
"""

with open(inputFilename, 'r', encoding='utf-8') as file:
    inputContent = file.read()

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
    {
      "role": "system",
      "content": prompt
    },
    {
      "role": "user",
      "content": inputContent
    }
	]
)

# Accessing the correct part of the completion response
output = completion.choices[0].message.content

# Write the output to a file
with open(outputFilename, "w", encoding="utf-8") as file:
    file.write(output)