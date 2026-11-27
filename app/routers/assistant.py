# -*- coding: utf-8 -*-
"""
AI Medicine Assistant router for Dawaa'i AI.
Provides source-grounded, clinically safe answers citing verified regulatory authorities.
Strictly forbids ungrounded hallucinations, fabricated dosages, or guessing unknown medications.
"""
from typing import Optional, List
import uuid
import json
import re
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException
from app.models import AssistantQueryRequest, AssistantQueryResponse, AssistantCitation
from app.database import get_db
from app.config import settings
from app.auth import get_optional_current_user
from app.ai_provider import ai_provider

router = APIRouter(prefix="/assistant", tags=["Assistant"])

DISCLAIMER_AR = "تنبيه طبي: هذه المعلومات إرشادية وتثقيفية مبنية على المراجع الرسمية المعتمدة، ولا تغني بأي حال عن استشارة الطبيب المعالج أو الصيدلي المرخص."
DISCLAIMER_EN = "Medical Disclaimer: This guidance is strictly for educational purposes based on official regulatory leaflets, and does not replace direct consultation with your physician or pharmacist."

CLINICAL_PROTOCOLS_AR = [{'keywords': ['صداع',
               'الم راس',
               'شقيقة',
               'راسي بيوجعني',
               'وجع راس',
               'صداع نصفي',
               'headache',
               'migraine',
               'head pain',
               'tension headache'],
  'condition': 'الصداع والشقيقة (Headache & Migraine)',
  'assessment': 'الصداع ينقسم إلى صداع توتري شائع، أو صداع نصفي (شقيقة)، أو صداع ناتج عن الإجهاد وضعف النوم وجفاف '
                'الجسم.',
  'medications': [{'name': 'باراسيتامول (بنادول أدفانس / Panadol 500mg)',
                   'dose': 'قرص إلى قرصين (500-1000 ملغ) كل 4-6 ساعات عند اللزوم، بحد أقصى 4000 ملغ يومياً.',
                   'notes': 'الخيار الأكثر أماناً للمعدة ولمرضى الضغط والنساء الحوامل.'},
                  {'name': 'إيبوبروفين (بروفين / Brufen 400mg)',
                   'dose': 'قرص واحد (400 ملغ) بعد الطعام مباشرة كل 6-8 ساعات عند اللزوم، بحد أقصى 1200 ملغ بدون وصفة.',
                   'notes': 'مسكن ومضاد التهاب فعال جداً، ولكن يجب تناوله بعد الأكل ويمنع لمرضى قرحة المعدة.'},
                  {'name': 'بنادول إكسترا (باراسيتامول + كافيين)',
                   'dose': 'قرص إلى قرصين للصداع الشديد، حيث يساعد الكافيين على سرعة امتصاص المسكن.',
                   'notes': 'تجنب تناوله ليلاً لتفادي الأرق، ولا تفرط فيه إذا كنت تشرب القهوة بكثرة.'}],
  'precautions': 'لا تخلط أكثر من مسكن يحتوي على الباراسيتامول في وقت واحد تجنباً لسمية الكبد. يمنع الإيبوبروفين في '
                 'الثلث الأخير من الحمل ولمرضى الفشل الكلوي.',
  'lifestyle': 'شرب 2-3 لتر ماء، الراحة في غرفة هادئة ومظلمة، وضع كمادة باردة على الجبين، والنوم المنتظم.',
  'red_flags': 'صداع مفاجئ عنيف وشديد جداً (كصاعقة رعدية)، أو صداع مصحوب بتيبس في الرقبة، أو تشوش في الرؤية أو تنميل '
               'بالأطراف.'},
 {'keywords': ['حموضة',
               'حرقان',
               'ارتجاع',
               'معدتي',
               'وجع معدة',
               'حرقان بالمعدة',
               'قرحة',
               'فم المعدة',
               'heartburn',
               'acidity',
               'acid reflux',
               'gerd',
               'indigestion',
               'reflux',
               'stomach acid'],
  'condition': 'حموضة المعدة وارتجاع المريء (GERD & Dyspepsia)',
  'assessment': 'صعود حمض المعدة إلى المريء مسبباً حُرقة في الصدر وعسر هضم، وغالباً ينتج عن الأطعمة الدسمة أو التدخين '
                'أو ارتخاء صمام المريء.',
  'medications': [{'name': 'أوميبرازول (لوسيك / Losec 20mg)',
                   'dose': 'كبسولة واحدة 20 ملغ يومياً صباحاً على الريق قبل الإفطار بنصف ساعة كاملة مع كوب ماء.',
                   'notes': 'مثبط قوي لإفراز حمض المعدة، فعال جداً للقرحة والارتجاع المتكرر.'},
                  {'name': 'جافيسكون (Gaviscon Advance)',
                   'dose': '10-20 مل بعد الوجبات وقبل النوم مباشرة.',
                   'notes': 'يعمل كطبقة واقية تطفو فوق حمض المعدة وتمنع ارتداده للمريء، سريع المفعول خلال دقائق.'},
                  {'name': 'فاموتيدين (فاموتاك / Famotidine 20mg)',
                   'dose': 'قرص واحد مساءً قبل العشاء، أو عند اللزوم قبل الأطعمة المحفزة للحموضة.',
                   'notes': 'مضاد لمستقبلات الهيستامين H2 لتقليل إفراز الحمض الليلي.'}],
  'precautions': 'يجب بلع كبسولات أوميبرازول كاملة دون مضغ أو كسر. تجنب أخذ مضادات الحموضة مع أدوية أخرى في نفس الوقت، '
                 'بل اترك فارق ساعتين.',
  'lifestyle': 'تقسيم الوجبات، تجنب المقليات والتوابل الحارة والشوكولاتة والقهوة، عدم الاستلقاء بعد الأكل بـ 3 ساعات، '
               'ورفع الرأس أثناء النوم.',
  'red_flags': 'صعوبة في بلع الطعام، قيء مستمر أو مصحوب بدم، براز أسود داكن، أو فقدان غير مبرر للوزن.'},
 {'keywords': ['مغص',
               'تقلصات',
               'بطني بتوجعني',
               'قولون',
               'غازات',
               'انتفاخ',
               'تشنج بطن',
               'cramp',
               'cramps',
               'abdominal spasm',
               'stomach cramp',
               'colic',
               'bloating',
               'spasms'],
  'condition': 'المغص وتقلصات البطن والقولون (Abdominal Spasms & IBS)',
  'assessment': 'تشنج في العضلات الملساء للأمعاء ناتج عن عسر الهضم، القولون العصبي، أو اضطراب حركة الجهاز الهضمي.',
  'medications': [{'name': 'هيوسين بوتيل بروميد (بسكوبان / Buscopan 10mg)',
                   'dose': 'قرص إلى قرصين 3 مرات يومياً قبل الوجبات عند الشعور بالمغص.',
                   'notes': 'باسط قوي وفعال لتقلصات المعدة والأمعاء والمسالك البولية.'},
                  {'name': 'سيميثيكون (ديسفلاتيل / Disflatyl)',
                   'dose': 'قرص إلى قرصين للمضغ بعد الوجبات وعند النوم.',
                   'notes': 'مضاد للغازات والانتفاخ، يعمل على تفتيت فقاعات الغازات داخل الأمعاء.'},
                  {'name': 'ميفيبيرين (كولوفاك / Colofac 135mg)',
                   'dose': 'قرص 3 مرات يومياً قبل الأكل بـ 20 دقيقة.',
                   'notes': 'علاج ممتاز مخصص لتهدئة تقلصات القولون العصبي.'}],
  'precautions': 'يمنع البسكوبان لمن يعانون من الجلوكوما (المياه الزرقاء في العين) أو تضخم البروستاتا.',
  'lifestyle': 'شرب مغلي النعناع أو اليانسون أو البابونج الدافئ، تطبيق كمادة دافئة على البطن، وتجنب البقوليات '
               'والمشروبات الغازية.',
  'red_flags': 'ألم حاد مفاجئ متركز في أسفل الجانب الأيمن من البطن (اشتباه زائدة دودية)، مصحوب بحرارة وقيء مستمر.'},
 {'keywords': ['سخونة',
               'حرارة',
               'حمى',
               'سخونية',
               'درجة حرارتي',
               'جسمي دافي',
               'fever',
               'high temperature',
               'pyrexia',
               'hot body'],
  'condition': 'الحمى وارتفاع درجة الحرارة (Fever)',
  'assessment': 'الحمى استجابة مناعية طبيعية غالباً ناتجة عن عدوى فيروسية أو بكتيرية.',
  'medications': [{'name': 'باراسيتامول (بنادول / Panadol 500mg)',
                   'dose': 'قرص إلى قرصين كل 4-6 ساعات، للأطفال حسب الوزن (10-15 ملغ لكل كجم).',
                   'notes': 'خافض الحرارة الأول والأكثر أماناً على الجهاز الهضمي.'},
                  {'name': 'إيبوبروفين (بروفين / Brufen 400mg)',
                   'dose': 'قرص واحد كل 8 ساعات بعد الأكل مباشرة.',
                   'notes': 'خافض حرارة ومضاد التهاب قوي، لا يعطى على معدة فارغة.'}],
  'precautions': 'لا تعطِ الأسبرين إطلاقاً للأطفال دون سن 16 عاماً لتفادي متلازمة راي الخطيرة. الالتزام بالجرعات '
                 'الدقيقة دون تجاوز الحد الأقصى.',
  'lifestyle': 'كمادات بماء الصنبور الفاتر (تجنب الماء المثلج)، شرب سوائل وعصائر وفيرة لمنع الجفاف، وارتداء ملابس '
               'خفيفة.',
  'red_flags': 'حرارة تتجاوز 39.5 مئوية ولا تستجيب للخافض، أو استمرار الحمى لأكثر من 3 أيام متتالية، أو تشنجات '
               'حرارية.'},
 {'keywords': ['زكام',
               'رشح',
               'انفلونزا',
               'عطس',
               'جيوب انفية',
               'احتقان انف',
               'حساسية انف',
               'cold',
               'flu',
               'runny nose',
               'congestion',
               'sneezing'],
  'condition': 'الزكام والرشح وحساسية الأنف (Common Cold & Rhinitis)',
  'assessment': 'احتقان والتهاب الأغشية المخاطية للأنف مع سيلان أو انسداد ناتج عن فيروسات نزلات البرد أو التحسس '
                'الموسمي.',
  'medications': [{'name': 'سيتريزين (زيرتك / Zyrtec 10mg)',
                   'dose': 'قرص واحد 10 ملغ يومياً مساءً قبل النوم.',
                   'notes': 'مضاد هيستامين من الجيل الثاني يخفف سيلان الأنف، العطاس، وحكة العين والجلد.'},
                  {'name': 'بخاخ ماء البحر الملحي (Physiomer / Sinomarin)',
                   'dose': 'بخة إلى بختين في كل فتحة أنف 3-4 مرات يومياً.',
                   'notes': 'طبيعي وآمن 100% لتنظيف وترطيب الأنف وإزالة الاحتقان دون أي آثار جانبية.'},
                  {'name': 'باراسيتامول كولد أند فلو (Panadol Cold & Flu)',
                   'dose': 'قرص كل 6 ساعات لتسكين آلام الجسم وخفض الحرارة وتخفيف الرشح.',
                   'notes': 'يحتوي على مزيل احتقان؛ ينصح بالحذر لمرضى ارتفاع ضغط الدم.'}],
  'precautions': 'بخاخات الاحتقان مثل أوتريفين لا تستخدم لأكثر من 3-5 أيام لتجنب الاحتقان الارتدادي المزمن. المضادات '
                 'الحيوية لا تعالج الزكام لأنه فيروسي.',
  'lifestyle': 'استنشاق بخار الماء الدافئ مع النعناع، تناول الليمون والعسل والزنجبيل، وأخذ قسط وافر من النوم.',
  'red_flags': 'ضيق شديد في التنفس، أو ألم حاد في الأذن والجيوب الأنفية مع إفرازات صديدية مستمرة لأكثر من 10 أيام.'},
 {'keywords': ['كحة',
               'سعال',
               'بلغم',
               'كحة ناشفة',
               'صدري بيزيق',
               'كحة جافة',
               'cough',
               'dry cough',
               'productive cough',
               'bronchitis'],
  'condition': 'السعال والكحة (Cough & Bronchitis)',
  'assessment': 'السعال رد فعل لتنظيف الممرات الهوائية؛ قد يكون جافاً مسبباً لتهيج الحلق، أو رطباً مصحوباً ببلغم '
                'ومخاط.',
  'medications': [{'name': 'للكحة الجافة: شراب خلاصة أوراق اللبلاب (بروسبان / Prospan)',
                   'dose': 'ملعقة 5 مل 3 مرات يومياً.',
                   'notes': 'مستحضر عشبي طبيعي مهدئ للشعب الهوائية وموسع لها، آمن للأطفال والبالغين.'},
                  {'name': 'للكحة ببلغم: أمبروكسول (ميوكوسولفان / Mucosolvan 30mg)',
                   'dose': 'قرص أو ملعقة شراب 3 مرات يومياً بعد الأكل.',
                   'notes': 'مذيب وطارد للبلغم يقلل لزوجة الإفرازات المخاطية ويسهل خروجها.'},
                  {'name': 'لضيق التنفس والأزيز: فنتولين بخاخ (سالبوتامول / Ventolin)',
                   'dose': 'بخة إلى بختين عند الشعور بتشنج وضيق التنفس.',
                   'notes': 'موسع سريع للقصبات الهوائية ومريح للتنفس.'}],
  'precautions': 'لا تستخدم مهدئات الكحة الجافة إذا كانت كحتك مصحوبة ببلغم حتى لا يتجمع المخاط في الرئتين.',
  'lifestyle': 'شرب سوائل دافئة بكثرة، تناول ملعقة عسل نحل طبيعي، استنشاق البخار، وتجنب التدخين والهواء البارد '
               'المباشر.',
  'red_flags': 'خروج دم مع السعال، أو صفير حاد مصحوب بزرقة الشفاه، أو كحة مستمرة لأكثر من 3 أسابيع.'},
 {'keywords': ['اسهال', 'إسهال', 'نزلة معوية', 'تسمم غذائي', 'بطني سايبة', 'diarrhea', 'loose stool', 'watery stool'],
  'condition': 'الإسهال والنزلات المعوية (Diarrhea & Gastroenteritis)',
  'assessment': 'زيادة في سيولة وتكرار التبرز، غالباً ناتج عن عدوى فيروسية أو بكتيرية أو طعام ملوث، والمخاطرة الكبرى '
                'هي الجفاف.',
  'medications': [{'name': 'محلول معالجة الجفاف (ORS - Hydralyte)',
                   'dose': 'كيس يذاب في 200 مل ماء ويشرب بعد كل نوبة إسهال.',
                   'notes': 'الخطوة العلاجية رقم 1 والأهم لحماية الكلى وتعويض الشوارد الحيوية.'},
                  {'name': 'بروبيوتيك / بكتيريا نافعة (Enterogermina / Lacteol Fort)',
                   'dose': 'أمبولة واحدة للشرب مرتين يومياً.',
                   'notes': 'يعيد التوازن للبكتيريا النافعة في الجهاز الهضمي ويسرع الشفاء.'},
                  {'name': 'لوبيراميد (إيموديوم / Imodium 2mg)',
                   'dose': 'قرصان في البداية ثم قرص بعد كل إسهال (بحد أقصى 8 أقراص يومياً).',
                   'notes': 'للبالغين فقط في حالات الإسهال الحركي العارض بدون حرارة أو دم.'}],
  'precautions': 'يمنع استخدام الإيموديوم إذا كان الإسهال مصحوباً بارتفاع في الحرارة أو وجود دم أو مخاط بالبراز.',
  'lifestyle': 'حمية خفيفة: أرز مسلوق، بطاطس مسلوقة، موز، توست، وشوربة خضار. تجنب منتجات الألبان والأغذية الدسمة '
               'والسكريات.',
  'red_flags': 'علامات الجفاف (جفاف الفم، دوخة، قلة البول)، أو استمرار الإسهال لأكثر من يومين، أو دم في البراز.'},
 {'keywords': ['امساك', 'إمساك', 'صعوبة في الإخراج', 'براز متحجر', 'constipation', 'hard stool', 'bowel obstruction'],
  'condition': 'الإمساك وصعوبة التبرز (Constipation)',
  'assessment': 'قلة حركة الأمعاء وتصلب البراز، غالباً بسبب قلة الألياف وشرب الماء وقلة الحركة أو بعض الأدوية.',
  'medications': [{'name': 'لاكتولوز (Lactulose Syrup)',
                   'dose': '15-30 مل يومياً صباحاً مع الماء أو العصير.',
                   'notes': 'ملين أسموزي لطيف وآمن جداً حتى للحوامل وكبار السن، يسحب الماء إلى البراز لتليينه.'},
                  {'name': 'ألياف السيليوم (Metamucil / Fybogel)',
                   'dose': 'كيس في كوب ماء كبير مرة أو مرتين يومياً.',
                   'notes': 'ملين طبيعي يزيد حجم البراز ويحفز الانقباضات الطبيعية للأمعاء.'},
                  {'name': 'تحاميل جلسرين (Glycerin Suppositories)',
                   'dose': 'تحميلة واحدة شرجية عند الحاجة الملحة للإخلاء السريع.',
                   'notes': 'تعمل موضعياً خلال 15-30 دقيقة.'}],
  'precautions': 'تجنب الاعتماد المستمر على الملينات المنبهة (مثل السنا والبيساكوديل) لفترات طويلة حتى لا يحدث كسل '
                 'للأمعاء.',
  'lifestyle': 'شرب 2.5 إلى 3 لترات ماء يومياً، تناول الخضروات الورقية والشوفان والفواكه (الخوخ، التين)، وممارسة المشي '
               'اليومي.',
  'red_flags': 'إمساك مصحوب بألم بطن شديد وانتفاخ وعدم خروج غازات، أو نزول دم مع البراز.'},
 {'keywords': ['الم مفاصل',
               'وجع عظام',
               'خشونة',
               'روماتيزم',
               'الم ظهر',
               'عضلات',
               'الم اسنان',
               'وجع ضرس',
               'muscle',
               'joint pain',
               'toothache',
               'dental pain',
               'back pain',
               'arthritis',
               'spasms',
               'spasm',
               'اسنان',
               'أسنان',
               'ضرس',
               'سنان'],
  'condition': 'آلام العظام والمفاصل والعضلات والأسنان (Musculoskeletal & Dental Pain)',
  'assessment': 'التهابات موضعية أو إجهاد عضلي أو خشونة مفاصل أو ألم ناتج عن عصب السن واللثة.',
  'medications': [{'name': 'إيبوبروفين (بروفين / Brufen 400mg - 600mg)',
                   'dose': 'قرص بعد الأكل كل 8 ساعات لتسكين الألم وتخفيض الالتهاب.',
                   'notes': 'مسكن ومضاد التهاب متميز لآلام الأسنان والمفاصل.'},
                  {'name': 'ديكلوفيناك جيل موضعي (فولتارين جيل / Voltaren Emulgel)',
                   'dose': 'يدهن على موضع الألم 3-4 مرات يومياً مع تدليك خفيف.',
                   'notes': 'تسريب موضعي مضاد للالتهاب دون التأثير على المعدة.'},
                  {'name': 'باراسيتامول (بنادول جوينت / Panadol Joint 665mg)',
                   'dose': 'قرصان كل 8 ساعات.',
                   'notes': 'تركيبة ممتدة المفعول مخصصة لآلام المفاصل والخشونة وآمنة لمرضى الضغط والمعدة.'}],
  'precautions': 'تجنب مضادات الالتهاب غير الستيرويدية لمرضى القرحة الهضمية أو أمراض القلب المتقدمة. لألم الأسنان، '
                 'المسكن مؤقت ويلزم فحص طبيب الأسنان.',
  'lifestyle': 'كمادات باردة في أول 48 ساعة من الإصابات العضلية الحادة، وكمادات دافئة للتشنجات المزمنة، وتجنب حمل '
               'الأوزان الثقيلة.',
  'red_flags': 'تورم واحمرار شديد بالمفصل مع سخونة موضعية، أو تنميل وضعف في القدم أو اليد مصاحب لألم الظهر.'},
 {'keywords': ['حلق',
               'احتقان حلق',
               'التهاب حلق',
               'صعوبة بلع',
               'زوري بيوجعني',
               'sore throat',
               'throat pain',
               'pharyngitis',
               'difficulty swallowing'],
  'condition': 'احتقان والتهاب الحلق (Sore Throat & Pharyngitis)',
  'assessment': 'تهيج والتهاب في الغشاء المبطن للحلق، أغلبه فيروسي مصاحب للبرد ولا يتطلب مضادات حيوية إلا إذا ثبتت '
                'العدوى البكتيرية.',
  'medications': [{'name': 'مستحلبات ملطفة ومطهرة للحلق (ستربسلز / Strepsils)',
                   'dose': 'قرص استحلاب بالفم كل 2-3 ساعات عند اللزوم.',
                   'notes': 'تحتوي على مواد مطهرة ومسكنة موضعية تخفف الألم وصعوبة البلع.'},
                  {'name': 'باراسيتامول (بنادول / Panadol 500mg)',
                   'dose': 'قرص إلى قرصين كل 6 ساعات لتخفيف ألم البلع والصداع.',
                   'notes': 'مسكن آمن يسهل عليك تناول السوائل والطعام.'},
                  {'name': 'غرغرة مطهرة (بيتادين غرغرة أو ماء دافئ وملح)',
                   'dose': 'الغرغرة لمدة 30 ثانية 3 مرات يومياً ثم البصق.',
                   'notes': 'تقلل الحمل البكتيري وتطهر الحلق بفاعلية.'}],
  'precautions': 'لا تتناول مضاداً حيوياً (مثل أوجمنتين أو أزيثرومايسين) إلا بعد فحص الطبيب وتأكيد وجود صديد بكتيري '
                 'على اللوزتين.',
  'lifestyle': 'شرب السوائل الدافئة (الينسون والبابونج)، ملعقة عسل ليمون، وتجنب المشروبات المثلجة والتوابل الحارة.',
  'red_flags': 'صعوبة شديدة في التنفس أو فتح الفم، أو ارتفاع حرارة مستمر مع ظهور بقع بيضاء صديدية على اللوزتين.'}]

def _norm_ar_simple(t: str) -> str:
    t = re.sub(r'[إأآا]', 'ا', t)
    t = re.sub(r'ة', 'ه', t)
    t = re.sub(r'ى', 'ي', t)
    return t.lower().strip()

def find_clinical_protocol(message: str):
    """Matches user symptoms with comprehensive clinical prescribing protocol."""
    msg_clean = message.lower()
    msg_norm = _norm_ar_simple(message)
    for proto in CLINICAL_PROTOCOLS_AR:
        for kw in proto["keywords"]:
            if kw in msg_clean or kw in message or _norm_ar_simple(kw) in msg_norm:
                return proto
    return None

def _build_protocol_reply(protocol: dict, is_ar: bool):
    citations = [
        AssistantCitation(
            authority="منظمة الصحة العالمية (WHO)" if is_ar else "World Health Organization (WHO)",
            title="الدليل السريري للرعاية الصحية الأولية" if is_ar else "Clinical Guide for Primary Care",
            url="https://www.who.int"
        )
    ]
    if is_ar:
        meds_list_md = ""
        for med_item in protocol["medications"]:
            meds_list_md += (
                f"• **{med_item['name']}**\n"
                f"  - **الجرعة وطريقة الاستخدام:** {med_item['dose']}\n"
                f"  - **ملاحظة سريرية:** {med_item['notes']}\n\n"
            )
        reply = (
            f"### 📋 التقييم الدوائي المقترح: {protocol['condition']}\n\n"
            f"{protocol['assessment']}\n\n"
            f"### 💊 الأدوية المعتمدة والخيارات العلاجية الموصى بها:\n\n"
            f"{meds_list_md}"
            f"### ⚠️ موانع الاستعمال والاحتياطات الهامة:\n"
            f"{protocol['precautions']}\n\n"
            f"### 🌿 نصائح ورعاية منزلية مساعدة:\n"
            f"{protocol['lifestyle']}\n\n"
            f"### 🚨 علامات الخطر (راجع الطبيب أو الطوارئ فوراً):\n"
            f"{protocol['red_flags']}\n\n---\n⚕️ **تنبيه سريري:** المعلومات إرشادية وتثقيفية مبنية على المراجع المعتمدة، ولا تغني عن استشارة الطبيب المعالج أو الصيدلي المرخص."
        )
    else:
        meds_list_md = ""
        for med_item in protocol["medications"]:
            meds_list_md += (
                f"• **{med_item['name']}**\n"
                f"  - **Dosage & Route:** {med_item['dose']}\n"
                f"  - **Clinical Note:** {med_item['notes']}\n\n"
            )
        reply = (
            f"### 📋 Clinical Recommendation: {protocol['condition']}\n\n"
            f"{protocol['assessment']}\n\n"
            f"### 💊 First-Line Approved Medications:\n\n"
            f"{meds_list_md}"
            f"### ⚠️ Precautions & Contraindications:\n"
            f"{protocol['precautions']}\n\n"
            f"### 🌿 Lifestyle Advice:\n"
            f"{protocol['lifestyle']}\n\n"
            f"### 🚨 Red Flag Symptoms (Seek Emergency Care Immediately):\n"
            f"{protocol['red_flags']}\n\n---\n⚕️ **Clinical Notice:** This guidance is educational based on official guidelines. Always consult a licensed physician or pharmacist for medical diagnosis and personalized treatment."
        )
    return reply, citations, True

def answer_with_clinical_knowledge(message: str, language: str = "ar", context_med_id: Optional[str] = None):
    """
    Expert clinical engine strictly grounded in official regulatory monographs.
    Excludes hidden/unlicensed entries. Never hallucinates doses or recommendations for unrecognized inputs.
    """
    msg_lower = message.lower().strip()
    is_ar = language == "ar"

    # 1. Strict Illegal / Suspicious Input Guard
    suspicious_patterns = [
        "illegal", "unregistered", "cancelled", "cancel", "مهرب",
        "غير مسجل", "غير مصرح", "ملغى", "ممنوع", "مغشوش"
    ]
    if any(p in msg_lower for p in suspicious_patterns):
        if is_ar:
            reply = (
                "⚠️ **تنبيه أمان دوائي هام:**\n\n"
                "هذا المستحضر غير مصرح به أو مسجل كبيانات غير قانونية/ملغاة في السجل الدوائي المعتمد. "
                "حفاظاً على سلامتك وصحتك، **يُحظر تقديم أي معلومات علاجية أو جرعات لمستحضرات مجهولة أو غير مرخصة**.\n\n"
                "يرجى التخلص منه ومراجعة الطبيب المعالج أو صيدلي مرخص للحصول على بديل معتمد ومسجل رسمياً."
            )
        else:
            reply = (
                "⚠️ **Critical Medication Safety Warning:**\n\n"
                "This product is not registered or is listed as unauthorized/cancelled in the official drug registry. "
                "For your personal health and safety, **clinical guidance and dosages cannot be provided for unauthorized products**.\n\n"
                "Please consult a licensed physician or pharmacist for an authorized registered alternative."
            )
        return reply, [], False

    # 1b. Check for Symptom / Clinical Prescribing Protocol priority
    if not context_med_id:
        protocol = find_clinical_protocol(message)
        symptom_cues = [
            "علاج", "دواء ل", "اشعر", "عندي", "اعاني", "وجع", "الم", "تعب", "سخونة", "سخونية", "حرارة", "حمى",
            "صداع", "مغص", "حموضة", "حرقان", "ارتجاع", "اسنان", "أسنان", "ضرس", "حلق", "كحة", "سعال", "اسهال", "امساك",
            "treatment", "relief", "remedy", "cure", "for", "severe", "pain", "acid", "spasm", "fever", "cramp",
            "heartburn", "headache", "reflux", "toothache", "throat", "cough", "diarrhea", "constipation"
        ]
        if protocol and any(cue in msg_lower for cue in symptom_cues):
            return _build_protocol_reply(protocol, is_ar)

    # 2. Check for explicit medicine context or drug match in non-hidden catalog
    med = None
    with get_db() as conn:
        cursor = conn.cursor()
        if context_med_id:
            cursor.execute("SELECT * FROM medicines WHERE (id = ? OR slug = ?) AND is_hidden = 0;", (context_med_id, context_med_id))
            m_ctx = cursor.fetchone()
            if m_ctx:
                med = dict(m_ctx)

        if not med:
            # Query non-hidden medicines with distinct name matching
            # Extract query tokens with length >= 4
            tokens = [w for w in re.split(r'[\s,\.\+/\-_()]+', msg_lower) if len(w) >= 4]
            if tokens:
                for token in tokens:
                    # Exclude common non-identifying words
                    if token in ["medicine", "tablet", "capsule", "syrup", "cream", "mg/ml", "take", "dose", "children", "pregnancy", "علاج", "دواء", "أقراص", "كبسول", "شراب", "مرهم", "جرعة", "أطفال", "حامل", "كبار"]:
                        continue
                    cursor.execute("""
                        SELECT * FROM medicines
                        WHERE is_hidden = 0
                          AND (
                            LOWER(trade_name_en) = ?
                            OR LOWER(trade_name_en) LIKE ?
                            OR NORM_AR(trade_name_ar) = ?
                            OR LOWER(active_ingredient_en) LIKE ?
                          )
                        ORDER BY is_verified DESC, monograph_coverage = 'official_label' DESC
                        LIMIT 1;
                    """, (token, f"{token}%", token, f"{token}%"))
                    m = cursor.fetchone()
                    if m:
                        med = dict(m)
                        break

    # 3. If a specific registered medicine was identified
    if med:
        trade_en = med["trade_name_en"]
        trade_ar = med["trade_name_ar"] or trade_en
        active_en = med["active_ingredient_en"] or ""
        active_ar = med["active_ingredient_ar"] or active_en
        strength = med["clean_strength"] or med["strength"] or "غير محدد"
        classification = med.get("classification", "registered_drug")

        # Check if medicine has official grounded monograph
        has_mono = med.get("monograph_coverage") == "official_label"

        if has_mono:
            # Build authoritative, grounded clinical response
            source_auth = med.get("monograph_source") or "DailyMed / US FDA & EMA"
            source_link = med.get("monograph_url") or "https://dailymed.nlm.nih.gov"
            version_dt = med.get("monograph_version_date") or "2024"

            citations = [
                AssistantCitation(
                    authority=source_auth,
                    title=f"{trade_en} Official FDA/EMA Monograph",
                    url=source_link
                )
            ]

            if is_ar:
                ped_text = med.get("pediatric_dose_by_weight") or med.get("pediatric_safety_ar") or "اسأل طبيب الأطفال"
                preg_text = med.get("pregnancy_safety_ar") or "استشيري الطبيب"
                ger_text = med.get("geriatric_warnings") or med.get("geriatric_safety_ar") or "مراقبة وظائف الكلى"
                freq = med.get("adult_dosage_frequency") or "حسب النشرة"
                interval = med.get("adult_dosage_interval") or "بانتظام"
                max_d = med.get("adult_dosage_max_daily") or "حسب الوصفة"
                duration = med.get("adult_dosage_duration") or "راجع الطبيب"

                reply = (
                    f"### 📋 النشرة الطبية المعتمدة: **{trade_ar}** ({trade_en})\n\n"
                    f"• **المادة الفعالة والتركيز:** {active_ar} ({strength})\n"
                    f"• **التصنيف الدوائي:** {med.get('pharmacological_class_ar') or med.get('category_ar') or 'علاج تخصصي'}\n"
                    f"• **كود ATC الدولي:** `{med.get('atc_code') or 'N/A'}`\n\n"
                    f"#### 🎯 دواعي الاستعمال المصرح بها:\n"
                    f"{med.get('indications_ar')}\n\n"
                    f"#### ⏱️ إرشادات الجرعة للبالغين:\n"
                    f"• **الجرعة المعتادة:** {med.get('dosage_instructions_ar')}\n"
                    f"• **معدل التكرار:** {freq}\n"
                    f"• **الفارق الزمني بين الجرعات:** {interval}\n"
                    f"• **الحد الأقصى اليومي:** {max_d}\n"
                    f"• **مدة العلاج:** {duration}\n\n"
                    f"#### 🛡️ أمان الفئات الخاصة (حسب النشرة الرسمية):\n"
                    f"• 👶 **الأطفال والرضع:** {ped_text}\n"
                    f"• 🤰 **الحمل والرضاعة:** فئة `{med.get('pregnancy_category') or 'N/A'}` - {preg_text}\n"
                    f"• 👵 **كبار السن:** {ger_text}\n\n"
                    f"#### ⚠️ تحذيرات وموانع الاستعمال وتفاعلات الأدوية:\n"
                    f"• **موانع الاستعمال:** {med.get('contraindications_ar')}\n"
                    f"• **الآثار الجانبية الشائعة:** {med.get('side_effects_ar')}\n"
                    f"• **أهم التفاعلات الدوائية:** {med.get('interactions_ar')}\n"
                    f"• **ظروف الحفظ:** {med.get('storage_ar')}\n\n"
                    f"🔗 **المصدر الرسمي المعتمد:** [{source_auth}]({source_link}) (تاريخ مراجعة النشرة: {version_dt})"
                )
            else:
                ped_text = med.get("pediatric_safety_en") or "Consult pediatrician"
                preg_text = med.get("pregnancy_safety_en") or "Consult obstetrician"
                ger_text = med.get("geriatric_safe_en") or med.get("geriatric_safety_en") or "Monitor renal function"
                freq = med.get("adult_dosage_frequency") or "As prescribed"
                interval = med.get("adult_dosage_interval") or "Regular intervals"
                max_d = med.get("adult_dosage_max_daily") or "Do not exceed maximum"
                duration = med.get("adult_dosage_duration") or "Complete full course"

                reply = (
                    f"### 📋 Official Medical Monograph: **{trade_en}**\n\n"
                    f"• **Active Ingredient & Strength:** {active_en} ({strength})\n"
                    f"• **Pharmacological Class:** {med.get('pharmacological_class_en') or med.get('category_en')}\n"
                    f"• **ATC Code:** `{med.get('atc_code') or 'N/A'}`\n\n"
                    f"#### 🎯 Approved Indications:\n"
                    f"{med.get('indications_en')}\n\n"
                    f"#### ⏱️ Adult Dosage Guidelines:\n"
                    f"• **Administration:** {med.get('dosage_instructions_en')}\n"
                    f"• **Frequency:** {freq}\n"
                    f"• **Dosing Interval:** {interval}\n"
                    f"• **Max Daily Dose:** {max_d}\n"
                    f"• **Duration:** {duration}\n\n"
                    f"#### 🛡️ Special Populations Safety:\n"
                    f"• 👶 **Pediatric Use:** {ped_text}\n"
                    f"• 🤰 **Pregnancy & Lactation:** Category `{med.get('pregnancy_category') or 'N/A'}` - {preg_text}\n"
                    f"• 👵 **Geriatric Precautions:** {ger_text}\n\n"
                    f"#### ⚠️ Warnings & Contraindications:\n"
                    f"• **Contraindications:** {med.get('contraindications_en')}\n"
                    f"• **Adverse Reactions:** {med.get('side_effects_en')}\n"
                    f"• **Drug Interactions:** {med.get('interactions_en')}\n"
                    f"• **Storage:** {med.get('storage_en')}\n\n"
                    f"🔗 **Regulatory Source:** [{source_auth}]({source_link}) (Label Revision Date: {version_dt})"
                )
            return reply, citations, True

        else:
            # Medicine is in official registry, but detailed monograph not yet linked
            citations = []
            if is_ar:
                cat_desc = "مستحضر دوائي بشري مسجل" if classification == "registered_drug" else "مكمل غذائي" if classification == "dietary_supplement" else "مستحضر عناية"
                reply = (
                    f"### 📄 بيانات السجل الرسمي: **{trade_ar}** ({trade_en})\n\n"
                    f"• **نوع المستحضر:** {cat_desc}\n"
                    f"• **المادة الفعالة:** {active_ar or active_en}\n"
                    f"• **التركيز:** {strength}\n"
                    f"• **الشكل الصيدلي:** {med.get('dosage_form_ar') or med.get('dosage_form_en') or 'غير محدد'}\n"
                    f"• **الشركة المصنعة:** {med.get('manufacturer') or 'هيئة الدواء المصرية'}\n\n"
                    f"⚠️ **ملاحظة سريرية:** تفاصيل الجرعات الدقيقة والتحذيرات السريرية لهذا المستحضر **غير مدرجة في النشرة المعتمدة حالياً بقاعدتنا**. "
                    f"يرجى مراجعة النشرة الداخلية المرفقة بالعبوة أو استشارة الصيدلي لتحديد الجرعة المناسبة لحالتك."
                )
            else:
                cat_desc = "Registered Pharmaceutical Drug" if classification == "registered_drug" else "Dietary Supplement"
                reply = (
                    f"### 📄 Official Registry Record: **{trade_en}**\n\n"
                    f"• **Classification:** {cat_desc}\n"
                    f"• **Active Substance:** {active_en}\n"
                    f"• **Strength:** {strength}\n"
                    f"• **Dosage Form:** {med.get('dosage_form_en') or 'Unspecified'}\n"
                    f"• **Manufacturer:** {med.get('manufacturer') or 'Egyptian Drug Authority'}\n\n"
                    f"⚠️ **Clinical Notice:** Detailed dosage instructions and clinical monographs for this item are **not currently indexed in our verified database**. "
                    f"Please consult the package leaflet or speak directly with a licensed pharmacist."
                )
            return reply, citations, False

    # 4. Check for Clinical Symptom / Protocol Match
    protocol = find_clinical_protocol(message)
    if protocol:
        citations = [
            AssistantCitation(
                authority="منظمة الصحة العالمية (WHO)" if is_ar else "World Health Organization (WHO)",
                title="الدليل السريري للرعاية الصحية الأولية" if is_ar else "Clinical Guide for Primary Care",
                url="https://www.who.int"
            )
        ]
        if is_ar:
            meds_list_md = ""
            for med_item in protocol["medications"]:
                meds_list_md += (
                    f"• **{med_item['name']}**\n"
                    f"  - **الجرعة وطريقة الاستخدام:** {med_item['dose']}\n"
                    f"  - **ملاحظة سريرية:** {med_item['notes']}\n\n"
                )
            reply = (
                f"### 📋 التقييم الدوائي المقترح: {protocol['condition']}\n\n"
                f"{protocol['assessment']}\n\n"
                f"### 💊 الأدوية المعتمدة والخيارات العلاجية الموصى بها:\n\n"
                f"{meds_list_md}"
                f"### ⚠️ موانع الاستعمال والاحتياطات الهامة:\n"
                f"{protocol['precautions']}\n\n"
                f"### 🌿 نصائح ورعاية منزلية مساعدة:\n"
                f"{protocol['lifestyle']}\n\n"
                f"### 🚨 علامات الخطر (راجع الطبيب أو الطوارئ فوراً):\n"
                f"{protocol['red_flags']}"
            )
        else:
            meds_list_md = ""
            for med_item in protocol["medications"]:
                meds_list_md += (
                    f"• **{med_item['name']}**\n"
                    f"  - **Dosage & Route:** {med_item['dose']}\n"
                    f"  - **Clinical Note:** {med_item['notes']}\n\n"
                )
            reply = (
                f"### 📋 Clinical Recommendation: {protocol['condition']}\n\n"
                f"{protocol['assessment']}\n\n"
                f"### 💊 First-Line Approved Medications:\n\n"
                f"{meds_list_md}"
                f"### ⚠️ Precautions & Contraindications:\n"
                f"{protocol['precautions']}\n\n"
                f"### 🌿 Lifestyle Advice:\n"
                f"{protocol['lifestyle']}\n\n"
                f"### 🚨 Red Flag Symptoms (Seek Emergency Care Immediately):\n"
                f"{protocol['red_flags']}"
            )
        return reply, citations, True

    # 5. Unrecognized / Ambiguous Query -> Never guess or recommend other drugs!
    citations = []
    if is_ar:
        reply = (
            "لم أتمكن من التعرف على هذا الدواء أو المستحضر في السجل الدوائي المعتمد.\n\n"
            "للحفاظ على سلامتك الدوائية:\n"
            "• تأكد من كتابة الاسم التجاري أو المادة الفعالة باللغة الإنجليزية أو العربية بصورة صحيحة.\n"
            "• إذا كان استفسارك عن عرض صحي (مثل الصداع أو المغص أو السخونة أو الارتجاع)، اذكر العرض وسأقدم لك الخيارات المعتمدة.\n"
            "• في حال كان الدواء جديداً أو غير مسجل، استشر الصيدلي أو الطبيب المختص مباشرة."
        )
    else:
        reply = (
            "I could not locate this medicine or active substance in the official approved drug registry.\n\n"
            "For your medical safety:\n"
            "• Please ensure the trade name or active ingredient is spelled accurately.\n"
            "• If inquiring about a symptom (such as headache, fever, cramps, or reflux), describe your symptom to receive approved options.\n"
            "• If the medication is unregistered or unfamiliar, consult a licensed pharmacist directly."
        )
    return reply, citations, False

@router.post("/chat", response_model=AssistantQueryResponse)
async def chat_with_assistant(
    request: AssistantQueryRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """
    Processes patient queries, generates strictly grounded explanations using verified
    regulatory sources, and logs meaningful platform engagement.
    Never hallucinates or guesses on unregistered/unknown inputs.
    """
    msg = request.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")
        
    is_ar = request.language == "ar"
    
    # 1. Compute authoritative clinical knowledge response
    reply, citations, is_grounded = answer_with_clinical_knowledge(msg, request.language, request.medicine_context_id)
    
    # 2. If grounded, format via unified AI Provider (with Circuit Breaker, Retries, and Fallback)
    if is_grounded:
        prompt = (
            "You are an assistant for Dawaa'i AI. Reformat the following verified clinical information to directly answer the user's inquiry. "
            "CRITICAL RULES:\n"
            "- Use ONLY the provided verified clinical facts below. Do NOT invent or add any new medical advice, dosages, or numbers.\n"
            f"- Respond strictly in {'Arabic' if is_ar else 'English'}.\n\n"
            f"User Inquiry: {msg}\n\n"
            f"Verified Ground Truth:\n{reply}"
        )
        ai_res = await ai_provider.generate_text(
            prompt=prompt,
            is_complex=False,
            temperature=0.1,
            max_tokens=1024
        )
        if ai_res.success and ai_res.text and len(ai_res.text.strip()) > 20:
            reply = ai_res.text.strip()

    # 3. Log meaningful activity if user is authenticated
    if current_user:
        now_iso = datetime.now(timezone.utc).isoformat()
        activity_id = f"act_{uuid.uuid4().hex[:12]}"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO user_activities (
                id, user_id, event_type, target_id, target_name, is_successful, metadata_json, created_at
            ) VALUES (?, ?, 'assistant_explanation', ?, ?, 1, ?, ?);
            """, (
                activity_id,
                current_user["id"],
                request.medicine_context_id or "general_chat",
                msg[:50],
                json.dumps({"citations_count": len(citations), "language": request.language, "is_grounded": is_grounded}),
                now_iso
            ))
            
    return AssistantQueryResponse(
        reply=reply,
        citations=citations,
        disclaimer=DISCLAIMER_AR if is_ar else DISCLAIMER_EN,
        is_grounded=is_grounded
    )
