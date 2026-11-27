/**
 * DAWAA'I AI (دوائي) — Complete Bilingual Internationalization Engine
 * Arabic (RTL) & English (LTR) with full interface translations
 */

const translations = {
  ar: {
    // Brand
    brand_name: "دوائي",
    brand_tagline: "افهم دواءك، بطريقة أوضح.",
    brand_category: "منصة ذكية وموثوقة لمعلومات الأدوية",

    // Navigation
    nav_home: "الرئيسية",
    nav_search: "بحث الأدوية",
    nav_scan: "مسح الدواء",
    nav_interactions: "التداخلات الدوائية",
    nav_leaflet: "قراءة النشرة",
    nav_assistant: "المساعد الذكي",
    nav_about: "عن المنصة",
    nav_signin: "تسجيل الدخول",
    nav_signout: "تسجيل الخروج",
    nav_profile: "حسابي",
    nav_admin: "إدارة التقييمات",

    // Hero Section
    hero_headline: "افهم دواءك بثقة.",
    hero_description: "اكتشف معلومات الأدوية، واقرأ النشرات الطبية، وافهم المصطلحات المعقدة من خلال تجربة ذكية باللغة العربية والإنجليزية.",
    hero_btn_search: "ابحث عن دواء",
    hero_btn_leaflet: "جرّب قراءة النشرة",
    hero_verified_badge: "بيانات سريرية موثقة ومعتمدة",

    // Live Dynamic Ticker
    ticker_ai_active: "🟢 الذكاء الاصطناعي السريري نشط ومحدث لحظياً",
    ticker_speed: "⚡ زمن المعالجة والتحليل الدوائي: 0.08 ثانية",
    ticker_interactions: "🛡️ نظام التحقق التلقائي من التفاعلات الدوائية والجرعات مفعّل",
    ticker_authorities: "📚 ربط مباشر مع سجلات هيئات الغذاء والدواء SFDA و FDA و EMA لعام 2026",

    // Quick Access Feature Cards
    quick_cards_title: "الخدمات الطبية الرقمية المتكاملة",
    quick_cards_subtitle: "أدوات ذكية متقدمة صُممت لتسهيل فهم الأدوية وحماية صحتك وسلامة عائلتك.",
    
    // Dynamic Drug Interaction Checker
    checker_badge: "أداة تفاعلية سريرية فورية",
    checker_title: "فاحص التفاعلات الدوائية والتآزر الحيوي",
    checker_subtitle: "اختر أو ادمج بين دوائين لفحص التوافق الحيوي ومخاطر التداخل فوراً وفق المعايير السريرية.",
    checker_quick_combos: "تركيبات شائعة للفحص السريع:",
    checker_med1: "الدواء الأول",
    checker_med2: "الدواء الثاني",
    checker_btn_check: "فحص التداخل",
    interactions_page_title: "فاحص التداخلات الدوائية والتآزر السريري",
    interactions_page_desc: "افحص فوراً أي تعارض أو تآزر بين دوائين بالاسم التجاري أو المادة الفعالة بدقة سريرية ومطابقة معتمدة من هيئات الغذاء والدواء.",

    card_search_title: "بحث الأدوية الموثق",
    card_search_desc: "ابحث في سجل الأدوية المعتمدة بالاسم التجاري أو العلمي، واطلع على الجرعات وموانع الاستعمال.",
    card_search_action: "ابدأ البحث الآن",

    card_scan_title: "مسح علبة الدواء (OCR)",
    card_scan_desc: "التقط صورة لعلبة أو شريط الدواء لاستخراج المادة الفعالة والتركيز فوراً عبر الذكاء الاصطناعي.",
    card_scan_action: "مسح العلبة",

    card_leaflet_title: "قارئ النشرة الطبية",
    card_leaflet_desc: "حوّل النشرات الطبية الطويلة والمعقدة إلى نقاط واضحة مع تبسيط المصطلحات التخصصية.",
    card_leaflet_action: "قراءة النشرة",

    card_assistant_title: "المساعد الطبي الذكي",
    card_assistant_desc: "اطرح أسئلتك الدوائية وتلقّ إجابات مدعومة بالمراجع الرسمية وإرشادات الأمان المعتمدة.",
    card_assistant_action: "تحدث مع المساعد",

    // How It Works
    how_it_works_title: "كيف تعمل منصة دوائي؟",
    how_it_works_subtitle: "ثلاث خطوات بسيطة للحصول على المعلومة الدوائية الموثوقة بكل وضوح.",
    step_1_title: "1. ابحث أو ارفع النشرة",
    step_1_desc: "أدخل اسم الدواء بالعربية أو الإنجليزية، أو صوّر علبة الدواء أو الصق نص النشرة الداخلية.",
    step_2_title: "2. استكشف البيانات المعتمدة",
    step_2_desc: "نظامنا يسترجع المعلومات الرسمية المصرحة من الهيئات الدوائية المعتمدة (SFDA, FDA, EMA).",
    step_3_title: "3. افهم الشرح المبسط",
    step_3_desc: "احصل على ملخص بلغة بسيطة ومفهومة يوضح الجرعة، موانع الاستعمال، والاحتياطات الحيوية.",
    step_interactive_pill: "اضغط لقراءة الدليل والخطوات بالتفصيل 📖",

    // Platform Benefits
    benefits_title: "لماذا يثق المرضى بمنصة دوائي؟",
    benefits_subtitle: "اضغط على أي ميزة للاطلاع على بروتوكول التحقق السريري ومعايير الأمان المتبعة.",
    benefit_1_title: "مصادر رسمية موثقة",
    benefit_1_desc: "لا نبتكر معلومات طبية من فراغ؛ كل تفصيل مرتبط بالنشرات الرسمية لهيئات الغذاء والدواء.",
    benefit_2_title: "ذكاء اصطناعي منضبط ومقيد",
    benefit_2_desc: "نماذجنا الطبية مصممة لتقديم شروحات لغوية آمنة ومحددة دون تخمين أو تشخيص طبي عشوائي.",
    benefit_3_title: "حماية تامة للخصوصية",
    benefit_3_desc: "لا نجمع أو نشارك سجلاتك الصحية الخاصة، وبيانات استخدامك مشفرة ومحمية بالكامل.",
    benefit_4_title: "تجربة عربية أصيلة",
    benefit_4_desc: "تم تصميم الواجهة والمصطلحات من الصفر لتدعم اللغة العربية بسلاسة تامة وتناسق طباعي.",
    benefit_interactive_pill: "معايير الاعتماد السريري 🔍",

    // Special Populations Safety
    safety_triangle_title: "ثلاثي الأمان للفئات الحساسة (الأطفال، الحوامل، كبار السن)",
    pop_pediatric: "أمان الأطفال والرضع",
    pop_pregnancy: "الحمل والرضاعة الطبيعية",
    pop_geriatric: "كبار السن (معايير بيرز)",

    // Trusted Sources
    trusted_sources_title: "مراجع وهيئات الاعتماد المعتمدة لدينا",
    trusted_sources_desc: "نعتمد على قواعد بيانات النشرات الدوائية الرسمية لهيئات الرقابة الصحية المعتمدة:",
    source_sfda: "الهيئة العامة للغذاء والدواء (SFDA)",
    source_fda: "إدارة الغذاء والدواء الأمريكية (US FDA)",
    source_ema: "وكالة الأدوية الأوروبية (EMA)",
    source_who: "منظمة الصحة العالمية (WHO)",

    // Statistics Section
    stats_title: "إحصائيات المنصة الحقيقية",
    stats_subtitle: "أرقام فعلية ومباشرة محسوبة بدقة من قاعدة البيانات الحية بدون أي أرقام مصطنعة.",
    stat_registered_users: "المستخدمون المسجلون",
    stat_verified_medicines: "الأدوية المعتمدة بالسجل",
    stat_processed_documents: "المستندات المعالجة بنجاح",
    stat_published_reviews: "التقييمات المنشورة",
    stat_average_rating: "متوسط التقييم العام",
    stat_zero_users: "نبدأ رحلتنا معًا: عدد المستخدمين المسجلين: 0",
    stat_zero_reviews: "كن أول من يشارك تجربته مع منصة دوائي",

    // Public Reviews Section
    reviews_title: "آراء وتقييمات المستخدمين الحقيقية",
    reviews_subtitle: "تجارب حقيقية يشاركها مستخدمو المنصة بعد تجربتهم العملية.",
    reviews_filter_all: "جميع التقييمات",
    reviews_filter_stars: "نجوم",
    reviews_empty_title: "كن أول من يشارك تجربته.",
    reviews_empty_desc: "لم يتم نشر أي تقييمات بعد في المنصة الجديدة. جرّب البحث وشاركنا رأيك الصادق!",
    // Dynamic Evaluation Visuals
    eval_badge: "مؤشر نبض وتفاعل المستخدمين الحي",
    eval_title: "رسومات بيانية حية تعبر عن تقييمات المرضى",
    eval_subtitle: "تتحدث الرسومات التعبيرية ونسبة الرضا لحظياً ومباشرة مع كل تقييم جديد يسجله المرضى.",
    eval_satisfaction_rate: "نسبة الرضا",
    eval_trust_status: "مستوى ثقة استثنائي",
    eval_trust_caption: "محسوبة من كافة مراجعات المرضى الحقيقية الموثقة في قاعدة البيانات.",
    eval_sentiment_breakdown: "توزيع مشاعر وتقييمات المراجعين (تفاعلي):",
    eval_prompt_rate: "جرّب المنصة وشارك تقييمك ليظهر في الرسم فوراً!",
    eval_btn_rate_now: "قيّمنا الآن",

    // First-Use Mandatory Review Dialog
    modal_review_title: "ما رأيك في تجربتك مع دوائي؟",
    modal_review_subtitle: "رأيك يساعدنا على تحسين الموقع وتقديم تجربة أفضل للجميع.",
    modal_review_rating_label: "اختر تقييمك (مطلوب):",
    rating_1: "سيئة جدًا",
    rating_2: "سيئة",
    rating_3: "مقبولة",
    rating_4: "جيدة جدًا",
    rating_5: "ممتازة",
    modal_review_comment_placeholder: "شاركنا رأيك أو اقتراحاتك الصادقة لتحسين المنصة...",
    modal_review_category_label: "مجال التقييم:",
    category_ease_of_use: "سهولة الاستخدام",
    category_medicine_search: "بحث الأدوية",
    category_leaflet_reader: "قارئ النشرة الطبية",
    category_ai_explanations: "شروحات المساعد الذكي",
    category_design: "تصميم المنصة",
    category_other: "أخرى",
    modal_review_consent: "أوافق على عرض هذا التقييم في قسم آراء المستخدمين مع إخفاء بياناتي الخاصة.",
    modal_review_submit: "إرسال التقييم",
    modal_review_later: "لاحقاً (تذكيري بعد قليل)",
    modal_review_success: "شكراً جزيلاً! تم تسجيل تقييمك بنجاح في قاعدة البيانات.",
    modal_review_error_select_rating: "يرجى اختيار التقييم (من 1 إلى 5 نجوم) قبل الإرسال.",

    // Login Page
    login_title: "مرحبًا بك في دوائي",
    login_subtitle: "سجّل الدخول للوصول إلى تجربتك الشخصية.",
    login_instant_btn: "⚡ تسجيل الدخول الفوري (حساب تجريبي نشط)",
    login_email_title: "أو سجّل الدخول بالبريد وكلمة المرور:",
    login_email_label: "البريد الإلكتروني",
    login_password_label: "كلمة المرور",
    login_submit_btn: "تسجيل الدخول",
    login_role_user: "👤 مستخدم تجريبي (مريض)",
    login_role_admin: "🛡️ مسؤول النظام (Admin)",
    login_google_btn: "المتابعة باستخدام Google",
    login_demo_btn: "دخول سريع للتجربة المحلية",
    login_demo_info: "يمكنك استخدام الحساب التجريبي لاختبار كافة المزايا والتقييمات على الفور.",
    login_terms_notice: "بتسجيل دخولك، فإنك توافق على شروط الاستخدام وسياسة الخصوصية لمنصة دوائي.",
    login_return_home: "العودة إلى الصفحة الرئيسية",

    // Onboarding Modal
    onboarding_title: "مرحباً بك في منصة دوائي AI",
    onboarding_step_1: "1. جميع المعلومات الطبية مرتبطة بمراجع معتمدة من هيئات الدواء الرسمية.",
    onboarding_step_2: "2. المساعد الذكي يقدم شروحات توضيحية ولا يقدم تشخيصات أو بدائل علاجية.",
    onboarding_step_3: "3. نطلب رأيك الصادق بعد أول استخدام فعلي لمساعدتنا على التطور المستمر.",
    onboarding_lang_prompt: "اختر لغتك المفضلة للمنصة:",
    onboarding_btn_start: "ابدأ استكشاف دوائي",

    // Medicine Search Page
    search_page_title: "دليل الأدوية المعتمدة والموثقة",
    search_input_placeholder: "ابحث بالاسم التجاري (مثل: بنادول)، المادة الفعالة، أو دواعي الاستعمال...",
    search_btn: "بحث",
    search_all_categories: "كافة الفئات الدوائية",
    search_results_count: "تم العثور على {count} أدوية معتمدة",
    search_verified_badge: "معتمد وموثق",
    search_view_details: "عرض تفاصيل الدواء والنشرة",
    search_empty: "لم يتم العثور على أدوية مطابقة لكلمات البحث. تأكد من صحة الاسم أو جرب اسماً بديلاً.",
    filter_all: "كافة المنتجات",
    filter_drugs: "أدوية بشرية مسجلة",
    filter_supplements: "مكملات غذائية وفيتامينات",
    filter_care: "مستحضرات عناية ونظافة",
    filter_devices: "مستلزمات وأجهزة",
    filter_pediatric: "مصرح للأطفال",
    filter_pregnancy: "آمن للحامل",
    sort_relevance: "الترتيب: الأنسب",
    sort_name_asc: "الاسم (أ - ي)",
    sort_price_asc: "السعر: الأقل أولاً",
    sort_price_desc: "السعر: الأعلى أولاً",

    // Medicine Details Modal
    med_active_ingredient: "المادة الفعالة والتركيز",
    med_category: "التصنيف الدوائي",
    med_dosage_form: "الشكل الصيدلاني",
    med_indications: "دواعي الاستعمال المعتمدة",
    med_dosage_instructions: "تعليمات الجرعة والاستخدام",
    med_contraindications: "موانع الاستعمال الهامة",
    med_side_effects: "الآثار الجانبية المحتملة",
    med_interactions: "التداخلات الدوائية والغذائية",
    med_pregnancy_safety: "درجة الأمان في الحمل والرضاعة",
    med_storage: "ظروف الحفظ والتخزين",
    med_official_source: "المرجع الرسمي المعتمد",
    med_ask_assistant: "استفسر عن هذا الدواء مع المساعد",

    // Scanner (OCR)
    scan_page_title: "مسح علبة الدواء بالذكاء الاصطناعي",
    scan_page_desc: "التقط صورة لعلبة الدواء أو ارفع صورة، وسيقوم النظام باستخراج المادة الفعالة ومطابقتها بالسجل الرسمي فوراً.",
    scan_dropzone: "اسحب صورة علبة الدواء هنا، أو انقر للاختيار من جهازك",
    scan_samples_label: "أو جرّب إحدى العينات الجاهزة:",
    scan_sample_panadol: "علبة بنادول 500 ملغ",
    scan_sample_augmentin: "علبة أوجمنتين 1 غرام",
    scan_sample_brufen: "علبة بروفين 400 ملغ",
    scan_btn_process: "تحليل ومطابقة الدواء",
    scan_btn_analyze: "تحليل بالذكاء الاصطناعي",
    scan_results_title: "نتائج فحص علبة الدواء",
    scan_detected_text: "النص المستخرج من العلبة:",
    scan_match_confidence: "نسبة المطابقة الدوائية:",

    // Leaflet Reader
    leaflet_page_title: "قارئ النشرة الطبية وتبسيط المصطلحات",
    leaflet_page_desc: "اقرأ النشرة الطبية مقسمة إلى بنود واضحة، مع ميزة التبسيط الفوري للمصطلحات الصيدلانية المعقدة.",
    leaflet_paste_label: "الصق نص النشرة الطبية هنا أو اختر عينة معتمدة:",
    leaflet_toggle_simplify: "تبسيط المصطلحات الطبية المعقدة",
    leaflet_btn_parse: "تحليل وتبسيط النشرة",
    leaflet_sample_panadol: "نشرة بنادول أدفانس",
    leaflet_sample_augmentin: "نشرة أوجمنتين 1 غرام",
    leaflet_sample_glucophage: "نشرة جلوكوفاج للسكري",

    // AI Assistant
    assistant_page_title: "المساعد الطبي الدوائي الذكي",
    assistant_page_desc: "مساعد رقمي موجه بالسلامة الدوائية، يقدم إجابات مبنية على النشرات المعتمدة مع ذكر المراجع الرسمية.",
    assistant_input_placeholder: "اكتب سؤالك الدوائي هنا (مثال: هل يمكن للحامل أخذ بنادول؟)...",
    assistant_btn_send: "إرسال",
    assistant_citations_title: "المراجع والهيئات المعتمدة للإجابة:",
    assistant_suggested_1: "هل البنادول آمن أثناء الحمل؟",
    assistant_suggested_2: "ما هي الجرعة الصحيحة لأوجمنتين 1 غرام؟",
    assistant_suggested_3: "ما هي موانع استخدام دواء بروفين؟",

    // Medical Disclaimer
    disclaimer_banner: "تنبيه طبي وقانوني هام: منصة دوائي AI منصة إرشادية وتثقيفية مبنية على النشرات الرسمية المعتمدة لهيئات الغذاء والدواء. المعلومات الواردة لا تغني إطلاقاً عن استشارة الطبيب البشري المختص أو الصيدلي المرخص، ولا يجوز الاعتماد عليها في تشخيص الأمراض أو تعديل الجرعات الدوائية.",

    // Footer
    footer_about_text: "دوائي AI — المنصة الذكية الرائدة لتيسير قراءة النشرات الطبية وفهم معلومات الأدوية باللغتين العربية والإنجليزية، وفق مراجع هيئات الدواء المعتمدة.",
    footer_quick_links: "روابط سريعة",
    footer_features: "الخدمات",
    footer_legal: "السياسات والشروط",
    footer_privacy: "سياسة الخصوصية",
    footer_terms: "شروط الاستخدام",
    footer_disclaimer_link: "إخلاء المسؤولية الطبية",
    footer_copyright: "© {year} دوائي AI (Dawaa'i). جميع الحقوق محفوظة.",

    reviews_anonymous_user: "مستخدم موثق",
    search_load_more: "تحميل المزيد من الأدوية",
    search_loading_more: "جارٍ تحميل المزيد...",
    category_all_therapeutic: "كافة التخصصات العلاجية",
    admin_health_title: "صحة النظام وخوادم الذكاء الاصطناعي",
    admin_health_subtitle: "مراقبة حية لحالة الخادم، وقاعدة البيانات، وقاطع التيار للموديلات",
    admin_health_server: "حالة الخادم",
    admin_health_db: "قاعدة البيانات",
    admin_health_primary_ai: "مزود الذكاء الاصطناعي الأساسي",
    admin_health_fallback_ai: "مزود الذكاء الاصطناعي الاحتياطي",
    admin_health_cache_ratio: "نسبة كاش التحليلات",
    admin_health_circuit: "قاطع التيار (Circuit Breaker)",
    admin_health_recent_errors: "سجل الأخطاء الأخيرة",
    admin_health_no_errors: "لا توجد أخطاء مسجلة، جميع الخدمات تعمل بكفاءة عالية.",

    // History & User Activities
    nav_history: "📜 سجلي ونشاطي",
    history_page_title: "سجلي ونشاطي الطبي",
    history_page_subtitle: "تتبع كافة الأدوية التي بحثت عنها، واستشاراتك، ومسح العلب المحفوظ في حسابك.",
    history_clear_btn: "مسح السجل",
    history_stat_total: "إجمالي الأنشطة",
    history_stat_searches: "عمليات البحث",
    history_stat_views: "الأدوية المستعرضة",
    history_stat_scans: "المسح والاستشارات",
    history_empty_title: "لا توجد أنشطة مسجلة في هذا القسم بعد",
    history_empty_desc: "كل عملية بحث أو فحص أو استشارة تقوم بها ستُحفظ في هذا السجل لتصل إليها في أي وقت.",
    history_btn_start_search: "ابحث في 17,167 دواء",
    history_btn_start_scan: "مسح علبة دواء",

    // Login & Register Showcase
    login_badge_showcase: "منصة المعلومات الدوائية المعتمدة 2026",
    login_hero_title: "رعايتك الصحية تبدأ بفهم دوائك بدقة وموثوقية",
    login_hero_desc: "انضم إلى دوائي AI للوصول إلى أدق قاعدة بيانات دوائية موثقة، وفحص التداخلات، ومسح العلب بالذكاء الاصطناعي مع حفظ كامل لسجل أبحاثك الدوائية.",
    login_feat_1_title: "17,167 دواء معتمد ومسجل",
    login_feat_1_desc: "دليل صيدلاني دقيق موثق من هيئة الدواء المصرية يشمل التركيزات والأشكال ودواعي الاستعمال.",
    login_feat_2_title: "ماسح العلب بالذكاء الاصطناعي",
    login_feat_2_desc: "التقط صورة علبة الدواء وتعرف فوراً على المادة الفعالة والجرعات والتحذيرات السريرية.",
    login_feat_3_title: "فحص التداخلات والتعارضات",
    login_feat_3_desc: "تحقق من أمان تناول دوائين معاً وتجنب التعارضات الحادة ومخاطر النزيف أو التسمم.",
    login_feat_4_title: "سجل شخصي آمن ومحفوظ",
    login_feat_4_desc: "كل عملية بحث أو فحص تقوم بها تُحفظ في حسابك لتراجع أدويتك وتاريخك في أي وقت.",
    auth_tab_register: "إنشاء حساب جديد",
    auth_tab_signin: "تسجيل الدخول",
    register_title: "أنشئ حسابك الطبي الآن",
    register_subtitle: "احفظ سجل أدويتك وبحوثاتك واستشاراتك الطبية لمتابعتها في أي وقت.",
    register_name_label: "الاسم الكامل",
    register_email_label: "البريد الإلكتروني",
    register_password_label: "كلمة المرور (اختياري)",
    register_role_label: "نوع الحساب",
    role_patient: "مريض / مستخدم",
    role_doctor: "طبيب / صيدلي",
    register_submit_btn: "✨ إنشاء حسابي والدخول للمنصة",
    signin_title: "مرحباً بعودتك",
    signin_subtitle: "سجّل دخولك لمتابعة سجل أدويتك واستشاراتك السابقة.",
    login_email_label: "البريد الإلكتروني",
    login_password_label: "كلمة المرور",
    login_submit_btn: "تسجيل الدخول",
    auth_or: "أو خيارات سريعة",
    login_instant_demo: "⚡ تجربة فورية بحساب مريض تجريبي",
    login_google_btn: "المتابعة باستخدام Google",
    login_guest_bypass: "تخطي والمتابعة كزائر دون تسجيل ←",

    // Registered Medicines Showcase
    showcase_badge: "✨ السجل الدوائي المعتمد 2026 (17,167 دواء)",
    showcase_title: "المعرض التفاعلي للأدوية المسجلة حسب التخصص العلاجي",
    showcase_subtitle: "استعراض تلقائي ذكي للأدوية المعتمدة ومواصفاتها السريرية",
    showcase_pause: "إيقاف مؤقت",
    showcase_play: "تشغيل تلقائي",
    showcase_prev: "السابق",
    showcase_next: "التالي",
    showcase_view_details: "عرض النشرة والتفاصيل الكاملة ↗",
    showcase_check_interactions: "فحص التداخلات لهذا الدواء ⚡",
    showcase_ask_assistant: "اسأل المساعد الطبي عن الدواء 🤖",
    showcase_cat_analgesics: "💊 مسكنات ومضادات التهاب",
    showcase_cat_antibiotics: "🛡️ مضادات حيوية وعدوى",
    showcase_cat_cardio: "❤️ القلب وضغط الدم",
    showcase_cat_diabetes: "🩸 السكري والتمثيل الغذائي",
    showcase_cat_respiratory: "🫁 الصدر والحساسية",
    showcase_cat_gi: "🧪 المعدة والجهاز الهضمي",

    // Hero Preview Card
    hero_sample_brand: "Panadol Advance 500mg",
    hero_sample_active_lbl: "المادة الفعالة:",
    hero_sample_active_val: "باراسيتامول (Paracetamol)",
    hero_sample_dose_lbl: "الجرعة المعتادة:",
    hero_sample_dose_val: "قرص إلى قرصين كل 4-6 ساعات (بحد أقصى 8 أقراص يومياً).",
    hero_sample_warn_lbl: "تنبيه أمان:",
    hero_sample_warn_val: "لا يكرر مع أدوية أخرى تحتوي على الباراسيتامول لتفادي سمية الكبد.",

    // Quick Combos
    combo_panadol_brufen: "💊 بنادول + بروفين",
    combo_aspirin_warfarin: "⚠️ أسبرين + وارفارين",
    combo_augmentin_probiotic: "💡 أوجمنتين + بروبيوتيك",
    combo_omeprazole_iron: "🔍 أوميبرازول + حديد",

    // Select options for drug combos
    opt_panadol: "بنادول (باراسيتامول 500 ملغ)",
    opt_brufen: "بروفين (إيبوبروفين 400 ملغ)",
    opt_aspirin: "أسبرين (حمض أسيتيل ساليسيليك 100 ملغ)",
    opt_warfarin: "وارفارين (مضاد تخثر 5 ملغ)",
    opt_augmentin: "أوجمنتين (أموكسيسيلين + كلافولانات 1 غرام)",
    opt_probiotic: "بروبيوتيك (بكتيريا نافعة 5 بليون)",
    opt_omeprazole: "أوميبرازول (مثبط مضخة البروتون 20 ملغ)",
    opt_iron: "مكملات الحديد (كبريتات الحديدوز 190 ملغ)",

    checker_default_res_title: "بنادول + بروفين: مزيج مسكن معتمد وآمن بحذر",
    checker_default_res_desc: "يعمل الدواءان عبر مسارات ألم مختلفة (باراسيتامول مركزياً + إيبوبروفين مضاد للالتهاب طرفياً). يمكن تناولهما بالتناوب عند الألم الشديد مع عدم تجاوز الجرعة القصوى لكل منهما.",

    // Category Chips Header in Search
    chips_heading: "🏷️ تصفح حسب التخصص العلاجي:",
    chips_subheading: "اختر تصنيفاً لعرض أدويته المعتمدة فوراً",

    // Classification Tabs
    filter_drugs: "أدوية بشرية مسجلة",
    filter_all: "كافة المنتجات",
    filter_supplements: "مكملات غذائية وفيتامينات",
    filter_care: "مستحضرات عناية ونظافة",
    filter_devices: "مستلزمات وأجهزة",

    // Sort Dropdown
    sort_relevance: "الترتيب: الأنسب",
    sort_name_asc: "الاسم (أ - ي)",
    sort_price_asc: "السعر: الأقل أولاً",
    sort_price_desc: "السعر: الأعلى أولاً",

    // Checkboxes
    filter_pediatric: "مصرح للأطفال",
    filter_pregnancy: "آمن للحامل",

    // About Page
    about_title: "عن منصة دوائي AI (Dawaa'i)",
    about_subtitle: "منصة رقمية رائدة لتيسير قراءة النشرات الطبية وفهم المعلومات الدوائية باللغتين العربية والإنجليزية.",
    about_sec1_title: "الرؤية والهدف السريري",
    about_sec1_desc: "تهدف منصة دوائي AI إلى تمكين المرضى ومقدمي الرعاية الصحية من الوصول السريع والموثوق لمعلومات الأدوية المسجلة، وتحويل النشرات الطبية ذات الصياغة المعقدة إلى شروحات مفهومة وآمنة تدعم اتخاذ القرارات الصحية السليمة دون المساس بسلامة المريض.",
    about_sec2_title: "منهجية البيانات والشفافية",
    about_sec2_desc: "تعتمد المنصة على قواعد البيانات المعتمدة لهيئات الغذاء والدواء مثل هيئة الدواء المصرية (EDA)، والهيئة العامة للغذاء والدواء (SFDA)، وإدارة الغذاء والدواء الأمريكية (US FDA)، ووكالة الأدوية الأوروبية (EMA). لا يقوم النظام باختراع أو استنتاج أي معلومات سريرية خارج المراجع الرسمية.",
    about_sec3_title: "الخصوصية والأمان",
    about_sec3_desc: "تلتزم المنصة بأعلى معايير الخصوصية الرقمية؛ لا يتم تخزين أو بيع أي بيانات صحية خاصة بالمستخدمين، وتخضع جميع التقييمات العامة لإشراف ورقابة تحمي الهوية الشخصية للمراجعين.",

    // Legal & Privacy Modals
    privacy_title: "سياسة الخصوصية وحماية البيانات",
    privacy_p1: "تحترم منصة دوائي AI خصوصية جميع الزوار والمستخدمين. نحن لا نقوم بجمع أو مشاركة السجلات الطبية الشخصية، ولا نقوم بربط سجلات التصفح بالهويات الواقعية.",
    privacy_p2: "تُستخدم جلسات تسجيل الدخول فقط لتقديم تجربة مخصصة وحفظ التفضيلات اللغوية، وتخضع التقييمات العامة لإخفاء الهوية عند النشر لحماية خصوصية المرضى.",
    terms_title: "شروط الاستخدام والمسؤولية",
    terms_p1: "منصة دوائي AI هي خدمة رقمية إرشادية وتثقيفية تهدف إلى تيسير قراءة النشرات الطبية المعتمدة. لا تشكل المعلومات المقدمة استشارة طبية أو تشخيصاً لمرض، ولا يجوز إيقاف أو تعديل أي علاج موصوف من قبل طبيب بشري مرخص استناداً إلى المنصة.",
    disclaimer_title: "إخلاء المسؤولية الطبية الصريحة",
    modal_close: "إغلاق",

    // Call to Action
    cta_title: "ابدأ الآن في فحص دواءك بأعلى درجات الدقة",
    cta_desc: "ابحث بالاسم التجاري، اقرأ النشرة الطبية بسهولة، أو اسأل المساعد الذكي في أي وقت.",
    cta_btn_search: "ابحث عن دواء الآن",
    cta_btn_assistant: "تحدث مع المساعد الذكي",

    // Search Category Options
    cat_opt_analgesics: "مسكنات الألم وخافضات الحرارة",
    cat_opt_antibiotics: "مضادات حيوية",
    cat_opt_nsaids: "مضادات الالتهاب",
    cat_opt_diabetes: "أدوية السكري",
    cat_opt_gi: "مضادات حموضة المعدة",
    cat_opt_cholesterol: "أدوية الكوليسترول والدهون",
    cat_opt_allergy: "مضادات الحساسية",
    cat_opt_respiratory: "موسعات الشعب الهوائية",

    // Scan Page
    scan_formats_supported: "يدعم صور JPG و PNG و WEBP لأي دواء في العالم",
    scan_auto_detect_badge: "📸 يتم التعرف تلقائياً على أي دواء عبر الذكاء الاصطناعي",
    scan_btn_choose_other: "اختيار صورة أخرى",
    scan_sample_pill_title: "اختبار فوري لأشهر الأدوية السريرية",
    scan_sample_omeprazole: "💊 أوميبرازول 20 ملغ (مضاد حموضة وقرحة)",
    scan_loading_main: "جارٍ تحليل الصورة بالذكاء الاصطناعي واستخراج البيانات الطبية الدقيقة...",
    scan_loading_sub: "يتم استخراج النصوص وفحص السجلات ومطابقة معايير هيئة الغذاء والدواء...",

    // Interactions
    inter_quick_combos_heading: "⚡ تركيبات سريرية شائعة للفحص السريع:",
    combo_plavix_omeprazole: "⛔ بلافيكس + أوميبرازول",
    combo_lipitor_klacid: "⚠️ ليبيتور + كلاسيد",
    inter_lbl_med1: "الدواء الأول (تجاري أو علمي):",
    inter_lbl_med2: "الدواء الثاني (تجاري أو علمي):",
    inter_btn_check: "فحص التداخل الدوائي الآن",

    // Chat / Assistant
    chat_welcome_title: "مرحباً بك في دوائي AI 👋",
    chat_welcome_desc: "أنا مساعدك الطبي الذكي. اسألني عن دواعي استخدام الأدوية، الجرعات، الأعراض الجانبية، أو التداخلات مع الأدوية الأخرى.",
    chat_prompt_headache: "عندي صداع شديد اخد ايه؟",
    chat_prompt_gerd: "علاج لحموضة المعدة والارتجاع",
    chat_prompt_cramps: "علاج للمغص والتقلصات",
    chat_prompt_cough: "علاج للكحة والبلغم",
    chat_prompt_cold: "علاج للزكام والرشح",
    chat_badge_official: "✓ مراجع رسمية معتمدة",
    chat_badge_privacy: "✓ خصوصية طبية مشفرة",
    chat_badge_bilingual: "✓ ثنائي اللغة (عربي / English)",

    // History Filters
    history_filter_all: "🌐 كافة الأنشطة",
    history_filter_searches: "🔍 عمليات البحث",
    history_filter_views: "💊 الأدوية المعروضة",
    history_filter_scans: "📷 مسح العلب",
    history_filter_assistant: "🤖 استشارات المساعد",
    history_loading_text: "جارٍ تحميل سجل نشاطك الطبي...",

    // Admin
    admin_btn_refresh: "🔄 تحديث المؤشرات",
    admin_health_checking: "جارٍ فحص استجابة السيرفر ونماذج الذكاء الاصطناعي...",
    admin_reviews_subtitle: "مراجعة آراء المستخدمين واعتمادها مع الحفاظ على النزاهة الإحصائية للتقييم الرقمي.",
    th_user: "المستخدم",
    th_rating: "التقييم",
    th_comment: "التعليق",
    th_category: "الفئة",
    th_status: "الحالة",
    th_action: "الإجراء",

    // Footer
    footer_link_registry: "سجل الأدوية المعتمدة",
    footer_rights: ". جميع الحقوق محفوظة.",
    footer_tagline: "افهم دواءك، بطريقة أوضح. • Understand Your Medicine.",
  },
  en: {
    // Brand
    brand_name: "Dawaa'i AI",
    brand_tagline: "Understand Your Medicine. Make Informed Decisions.",
    brand_category: "Intelligent Healthcare & Medicine Information Platform",

    // Navigation
    nav_home: "Home",
    nav_search: "Medicine Search",
    nav_scan: "Scan Medicine",
    nav_interactions: "Drug Interactions",
    nav_leaflet: "Leaflet Reader",
    nav_assistant: "AI Assistant",
    nav_about: "About",
    nav_signin: "Sign In",
    nav_signout: "Sign Out",
    nav_profile: "My Profile",
    nav_admin: "Moderate Reviews",

    // Hero Section
    hero_headline: "Understand Your Medicine with Confidence.",
    hero_description: "Explore medicine information, read medicine leaflets, and understand complex medical terminology through an intelligent bilingual experience.",
    hero_btn_search: "Search Medicines",
    hero_btn_leaflet: "Explore Leaflet Reader",
    hero_verified_badge: "Verified Clinical Regulatory Data",

    // Live Dynamic Ticker
    ticker_ai_active: "🟢 Clinical AI Assistant active & updated in real-time",
    ticker_speed: "⚡ Pharmacological query response time: 0.08s",
    ticker_interactions: "🛡️ Automated drug interaction and dosage safety engine enabled",
    ticker_authorities: "📚 Direct 2026 regulatory integration with SFDA, FDA & EMA catalogs",

    // Quick Access Feature Cards
    quick_cards_title: "Integrated Digital Health Services",
    quick_cards_subtitle: "Advanced intelligent tools crafted to clarify medicine information and safeguard your health.",

    // Dynamic Drug Interaction Checker
    checker_badge: "Instant Clinical Tool",
    checker_title: "Live Drug Interaction & Synergy Quick-Checker",
    checker_subtitle: "Select or combine two medications to immediately inspect compatibility & clinical risk.",
    checker_quick_combos: "Popular quick test combos:",
    checker_med1: "First Medication",
    checker_med2: "Second Medication",
    checker_btn_check: "Check Interaction",
    interactions_page_title: "Drug-Drug Interaction & Clinical Synergy Checker",
    interactions_page_desc: "Instantly evaluate pharmacodynamic interactions or synergies between two medications by brand or active ingredient according to official regulatory monographs.",

    card_search_title: "Verified Medicine Search",
    card_search_desc: "Search verified registry records by trade or generic name. Inspect approved dosages and contraindications.",
    card_search_action: "Search Medicines",

    card_scan_title: "Medicine Image Scanner (OCR)",
    card_scan_desc: "Scan packaging or blister strips to extract active ingredients and strength instantly with smart AI.",
    card_scan_action: "Scan Medicine Box",

    card_leaflet_title: "Leaflet Reader",
    card_leaflet_desc: "Transform lengthy clinical leaflets into concise, structured sections with simplified medical terms.",
    card_leaflet_action: "Read Leaflet",

    card_assistant_title: "AI Medicine Assistant",
    card_assistant_desc: "Ask medicine queries and receive answers grounded in official health authority guidelines.",
    card_assistant_action: "Chat with Assistant",

    // How It Works
    how_it_works_title: "How Dawaa'i AI Works",
    how_it_works_subtitle: "Three straightforward steps to clear, verified medicine understanding.",
    step_1_title: "1. Search or Upload a Leaflet",
    step_1_desc: "Search by English or Arabic name, capture a packaging photo, or paste patient leaflet text.",
    step_2_title: "2. Explore Verified Data",
    step_2_desc: "Our engine queries verified monographs approved by regulatory bodies (SFDA, FDA, EMA).",
    step_3_title: "3. Read Simplified Explanations",
    step_3_desc: "Review concise patient-friendly summaries highlighting dosages, contraindications, and key precautions.",
    step_interactive_pill: "Click to Read Step-by-Step Guide 📖",

    // Platform Benefits
    benefits_title: "Why Patients Rely on Dawaa'i AI",
    benefits_subtitle: "Click any feature to explore our clinical verification protocols and safety criteria.",
    benefit_1_title: "Identifiable Official Sources",
    benefit_1_desc: "No medical fabrications; every detail is tied directly to verified regulatory health monographs.",
    benefit_2_title: "Grounded & Constrained AI",
    benefit_2_desc: "Our models clarify language and never invent unverified therapeutic claims or diagnoses.",
    benefit_3_title: "Privacy First",
    benefit_3_desc: "We do not sell personal health histories; your activities remain encrypted and strictly protected.",
    benefit_4_title: "Seamless Bilingual Design",
    benefit_4_desc: "Engineered from the ground up to support both Arabic and English with natural typographic scales.",
    benefit_interactive_pill: "Clinical Standards 🔍",

    // Special Populations Safety
    safety_triangle_title: "Special Populations Safety Triangle",
    pop_pediatric: "Pediatric Safety",
    pop_pregnancy: "Pregnancy & Lactation",
    pop_geriatric: "Geriatric Safety (Beers Criteria)",

    // Trusted Sources
    trusted_sources_title: "Our Trusted Health Authority References",
    trusted_sources_desc: "Information is derived from authorized regulatory public medicine registries:",
    source_sfda: "Saudi Food and Drug Authority (SFDA)",
    source_fda: "US Food and Drug Administration (FDA)",
    source_ema: "European Medicines Agency (EMA)",
    source_who: "World Health Organization (WHO)",

    // Statistics Section
    stats_title: "Real Platform Usage Statistics",
    stats_subtitle: "Actual database aggregate metrics calculated live without any fabricated numbers.",
    stat_registered_users: "Registered Users",
    stat_verified_medicines: "Verified Medicine Records",
    stat_processed_documents: "Successfully Processed Documents",
    stat_published_reviews: "Published User Reviews",
    stat_average_rating: "Average User Rating",
    stat_zero_users: "Growing together: Registered users: 0",
    stat_zero_reviews: "Be the first to share your experience with Dawaa'i AI",

    // Public Reviews Section
    reviews_title: "Authentic Public User Reviews",
    reviews_subtitle: "Genuine feedback submitted by real users following actual platform engagement.",
    reviews_filter_all: "All Reviews",
    reviews_filter_stars: "Stars",
    reviews_empty_title: "Be the first to share your experience.",
    reviews_empty_desc: "No public reviews published yet on this fresh installation. Try searching and share your honest feedback!",
    reviews_anonymous_user: "Verified Patient",

    // Dynamic Evaluation Visuals
    eval_badge: "Live User Sentiment Pulse",
    eval_title: "Dynamic Live Patient Sentiment & Rating Visuals",
    eval_subtitle: "Emotion avatars and satisfaction gauge update live as users evaluate the platform.",
    eval_satisfaction_rate: "Satisfaction Rate",
    eval_trust_status: "Exceptional Trust Level",
    eval_trust_caption: "Calculated live from authentic database reviews.",
    eval_sentiment_breakdown: "User sentiment breakdown (Interactive):",
    eval_prompt_rate: "Try the platform and rate it to see your feedback reflected live!",
    eval_btn_rate_now: "Rate Us Now",

    // First-Use Mandatory Review Dialog
    modal_review_title: "How was your experience with Dawaa'i AI?",
    modal_review_subtitle: "Your feedback helps us improve the platform and make it more useful for everyone.",
    modal_review_rating_label: "Select your rating (required):",
    rating_1: "Very poor",
    rating_2: "Poor",
    rating_3: "Fair",
    rating_4: "Very good",
    rating_5: "Excellent",
    modal_review_comment_placeholder: "Share your honest feedback or suggestions to help us improve...",
    modal_review_category_label: "Review Category:",
    category_ease_of_use: "Ease of use",
    category_medicine_search: "Medicine search",
    category_leaflet_reader: "Leaflet reader",
    category_ai_explanations: "AI explanations",
    category_design: "Website design",
    category_other: "Other",
    modal_review_consent: "I consent to displaying this review publicly while keeping my private identity hidden.",
    modal_review_submit: "Submit Review",
    modal_review_later: "Remind me later",
    modal_review_success: "Thank you! Your feedback has been recorded in the database.",
    modal_review_error_select_rating: "Please select a star rating (1 to 5) before submitting.",

    // Login Page
    login_title: "Welcome to Dawaa'i AI",
    login_subtitle: "Sign in to access your personalized experience.",
    login_instant_btn: "⚡ Instant Demo Sign In (Active Account)",
    login_email_title: "Or sign in with email & password:",
    login_email_label: "Email Address",
    login_password_label: "Password",
    login_submit_btn: "Sign In",
    login_role_user: "👤 Demo Patient User",
    login_role_admin: "🛡️ Clinical Administrator (Admin)",
    login_google_btn: "Continue with Google (Local Mock)",
    login_demo_btn: "Quick Demo / Local Sign In",
    login_demo_info: "You can sign in with the local account to test all features and review journeys immediately.",
    login_terms_notice: "By signing in, you agree to Dawaa'i AI's Terms of Use and Privacy Policy.",
    login_return_home: "Return to Homepage",

    // Onboarding Modal
    onboarding_title: "Welcome to Dawaa'i AI",
    onboarding_step_1: "1. All medicine records cite official regulatory authorities (SFDA, FDA, EMA).",
    onboarding_step_2: "2. The AI assistant offers educational explanations, never clinical diagnosis.",
    onboarding_step_3: "3. We request your honest feedback after your first meaningful use to help us improve.",
    onboarding_lang_prompt: "Select your preferred language:",
    onboarding_btn_start: "Start Exploring",

    // Medicine Search Page
    search_page_title: "Verified Medicine Information Catalog",
    search_input_placeholder: "Search by trade name (e.g. Panadol), active ingredient, or indication...",
    search_btn: "Search",
    search_all_categories: "All Categories",
    search_results_count: "Found {count} verified medicine records",
    search_verified_badge: "Verified & Approved",
    search_view_details: "View Full Leaflet & Clinical Details",
    search_empty: "No matching medicines found. Check spelling or try a generic ingredient name.",
    filter_all: "All Products",
    filter_drugs: "Registered Pharmaceuticals",
    filter_supplements: "Dietary Supplements & Vitamins",
    filter_care: "Personal Care & Hygiene",
    filter_devices: "Medical Devices & Kits",
    filter_pediatric: "Pediatric Approved",
    filter_pregnancy: "Pregnancy Safe",
    sort_relevance: "Sort: Relevance",
    sort_name_asc: "Name (A - Z)",
    sort_price_asc: "Price: Low to High",
    sort_price_desc: "Price: High to Low",

    // Medicine Details Modal
    med_active_ingredient: "Active Ingredient & Strength",
    med_category: "Therapeutic Category",
    med_dosage_form: "Dosage Form",
    med_indications: "Approved Medical Indications",
    med_dosage_instructions: "Dosage & Administration Guidelines",
    med_contraindications: "Important Contraindications",
    med_side_effects: "Potential Adverse Effects",
    med_interactions: "Drug & Food Interactions",
    med_pregnancy_safety: "Pregnancy & Lactation Safety",
    med_storage: "Storage Conditions",
    med_official_source: "Official Regulatory Authority",
    med_ask_assistant: "Ask AI Assistant About This Drug",

    // Scanner (OCR)
    scan_page_title: "AI Medicine Box & Packaging Scanner",
    scan_page_desc: "Capture a photo of your medicine box or upload an image to identify active ingredients and match verified records.",
    scan_dropzone: "Drag and drop medicine packaging photo here, or click to browse",
    scan_samples_label: "Or try a pre-configured sample:",
    scan_sample_panadol: "Panadol 500mg Box",
    scan_sample_augmentin: "Augmentin 1g Box",
    scan_sample_brufen: "Brufen 400mg Box",
    scan_btn_process: "Analyze & Match Medicine",
    scan_btn_analyze: "Analyze with AI",
    scan_results_title: "Package Inspection Results",
    scan_detected_text: "Extracted Packaging Text:",
    scan_match_confidence: "Pharmacological Match Confidence:",

    // Leaflet Reader
    leaflet_page_title: "Leaflet Reader & Medical Simplifier",
    leaflet_page_desc: "Read official patient information leaflets categorized clearly, with plain-language medical term simplification.",
    leaflet_paste_label: "Paste leaflet text here or select a verified template:",
    leaflet_toggle_simplify: "Simplify Complex Medical Terminology",
    leaflet_btn_parse: "Parse & Simplify Leaflet",
    leaflet_sample_panadol: "Panadol Advance Leaflet",
    leaflet_sample_augmentin: "Augmentin 1g Leaflet",
    leaflet_sample_glucophage: "Glucophage Diabetes Leaflet",

    // AI Assistant
    assistant_page_title: "AI Medicine Guidance Assistant",
    assistant_page_desc: "A safety-focused medical AI assistant that explains medicine leaflets citing regulatory sources.",
    assistant_input_placeholder: "Type your medicine inquiry (e.g., Is Panadol safe during pregnancy?)...",
    assistant_btn_send: "Send",
    assistant_citations_title: "Verified Regulatory Citations:",
    assistant_suggested_1: "Is Panadol safe during pregnancy?",
    assistant_suggested_2: "What is the recommended dose for Augmentin 1g?",
    assistant_suggested_3: "What are the contraindications for Brufen?",

    // Medical Disclaimer
    disclaimer_banner: "Important Medical & Legal Notice: Dawaa'i AI provides educational guidance based on official public health authority monographs. This platform does NOT substitute for professional consultation with a licensed medical practitioner or registered pharmacist. Never use this information to self-diagnose or alter prescription medication regimens.",

    // Footer
    footer_about_text: "Dawaa'i AI — The premier bilingual healthcare platform for understanding medicine leaflets and pharmacological terminology with verified regulatory citations.",
    footer_quick_links: "Quick Navigation",
    footer_features: "Features",
    footer_legal: "Policies & Legal",
    footer_privacy: "Privacy Policy",
    footer_terms: "Terms of Use",
    footer_disclaimer_link: "Medical Disclaimer",
    reviews_anonymous_user: "Verified User",
    search_load_more: "Load More Medicines",
    search_loading_more: "Loading more medicines...",
    category_all_therapeutic: "All Therapeutic Specialties",
    admin_health_title: "System & AI Providers Health",
    admin_health_subtitle: "Real-time monitoring of server, database, and AI circuit breakers",
    admin_health_server: "Server Status",
    admin_health_db: "Database",
    admin_health_primary_ai: "Primary AI Provider",
    admin_health_fallback_ai: "Fallback AI Provider",
    admin_health_cache_ratio: "Analytics Cache Hit Ratio",
    admin_health_circuit: "Circuit Breaker",
    admin_health_recent_errors: "Recent Errors Log",
    admin_health_no_errors: "No errors recorded. All systems operational.",
    // History & User Activities
    nav_history: "📜 My Activity History",
    history_page_title: "My Medical & Activity History",
    history_page_subtitle: "Track all medicines you searched for, consultations, and box scans saved in your account.",
    history_clear_btn: "Clear History",
    history_stat_total: "Total Activities",
    history_stat_searches: "Medicine Searches",
    history_stat_views: "Viewed Medicines",
    history_stat_scans: "Scans & Consultations",
    history_empty_title: "No activities recorded in this section yet",
    history_empty_desc: "Every medicine search, scan, or consultation you perform is saved in this secure log for your review.",
    history_btn_start_search: "Search 17,167 Medicines",
    history_btn_start_scan: "Scan Medicine Box",

    // Login & Register Showcase
    login_badge_showcase: "Verified Clinical Medicine Platform 2026",
    login_hero_title: "Your Health Begins with Accurate Medicine Understanding",
    login_hero_desc: "Join Dawaa'i AI to access the most accurate regulatory medicine database, interaction checks, and AI box scanning with full personal research tracking.",
    login_feat_1_title: "17,167 Verified Registered Medicines",
    login_feat_1_desc: "Precise pharmaceutical directory with dosages, formulations, and indications.",
    login_feat_2_title: "AI Medicine Packaging Scanner",
    login_feat_2_desc: "Capture a photo of the medicine box to instantly identify active ingredients, dosages, and clinical alerts.",
    login_feat_3_title: "Drug-Drug Interaction Checker",
    login_feat_3_desc: "Check the safety of combining two medications and prevent severe interactions and toxicity.",
    login_feat_4_title: "Safe & Persistent Personal History",
    login_feat_4_desc: "Every search or scan you perform is securely tracked in your profile for easy review anytime.",
    auth_tab_register: "Create Account",
    auth_tab_signin: "Sign In",
    register_title: "Create Your Medical Account",
    register_subtitle: "Save your medication queries, searches, and AI consultations to review them anytime.",
    register_name_label: "Full Name",
    register_email_label: "Email Address",
    register_password_label: "Password (Optional)",
    register_role_label: "Account Role",
    role_patient: "Patient / User",
    role_doctor: "Physician / Pharmacist",
    register_submit_btn: "✨ Create My Account & Enter Platform",
    signin_title: "Welcome Back",
    signin_subtitle: "Sign in to access your previous medicine search and consultation history.",
    login_email_label: "Email Address",
    login_password_label: "Password",
    login_submit_btn: "Sign In",
    auth_or: "Or Quick Options",
    login_instant_demo: "⚡ Instant Access with Demo Patient Account",
    login_google_btn: "Continue with Google",
    login_guest_bypass: "Skip & continue as guest without signing in →",

    // Registered Medicines Showcase
    showcase_badge: "✨ Verified Clinical Drug Registry 2026 (17,167 Drugs)",
    showcase_title: "Interactive Registered Medicines Showcase by Specialty",
    showcase_subtitle: "Intelligent automated presentation of verified medications & clinical indications",
    showcase_pause: "Pause",
    showcase_play: "Auto-Play",
    showcase_prev: "Previous",
    showcase_next: "Next",
    showcase_view_details: "View Full Leaflet & Details ↗",
    showcase_check_interactions: "Check Drug Interactions ⚡",
    showcase_ask_assistant: "Ask AI Assistant About This Drug 🤖",
    showcase_cat_analgesics: "💊 Analgesics & Pain",
    showcase_cat_antibiotics: "🛡️ Antibiotics & Infection",
    showcase_cat_cardio: "❤️ Cardiovascular & BP",
    showcase_cat_diabetes: "🩸 Diabetes & Metabolic",
    showcase_cat_respiratory: "🫁 Respiratory & Allergy",
    showcase_cat_gi: "🧪 Gastrointestinal & Acid",

    // Hero Preview Card
    hero_sample_brand: "Panadol Advance 500mg",
    hero_sample_active_lbl: "Active Ingredient:",
    hero_sample_active_val: "Paracetamol (Acetaminophen)",
    hero_sample_dose_lbl: "Standard Dosage:",
    hero_sample_dose_val: "1-2 tablets every 4-6 hours (max 8 tablets daily).",
    hero_sample_warn_lbl: "Safety Warning:",
    hero_sample_warn_val: "Do not combine with other paracetamol medications to prevent liver toxicity.",

    // Quick Combos
    combo_panadol_brufen: "💊 Panadol + Brufen",
    combo_aspirin_warfarin: "⚠️ Aspirin + Warfarin",
    combo_augmentin_probiotic: "💡 Augmentin + Probiotics",
    combo_omeprazole_iron: "🔍 Omeprazole + Iron",

    // Select options for drug combos
    opt_panadol: "Panadol (Paracetamol 500mg)",
    opt_brufen: "Brufen (Ibuprofen 400mg)",
    opt_aspirin: "Aspirin (Acetylsalicylic Acid 100mg)",
    opt_warfarin: "Warfarin (Anticoagulant 5mg)",
    opt_augmentin: "Augmentin (Amoxicillin + Clavulanate 1g)",
    opt_probiotic: "Probiotic (Beneficial Flora 5 Billion)",
    opt_omeprazole: "Omeprazole (PPI 20mg)",
    opt_iron: "Iron Supplement (Ferrous Sulfate 190mg)",

    checker_default_res_title: "Panadol + Brufen: Clinically Approved & Safe with Caution",
    checker_default_res_desc: "Both drugs work via distinct pain pathways (paracetamol centrally + ibuprofen peripherally). They can be alternated during acute pain while adhering to maximum daily limits.",

    // Category Chips Header in Search
    chips_heading: "🏷️ Browse by Therapeutic Specialty:",
    chips_subheading: "Select a specialty to instantly view its verified medicines",

    // Classification Tabs
    filter_drugs: "Registered Human Drugs",
    filter_all: "All Products",
    filter_supplements: "Dietary Supplements & Vitamins",
    filter_care: "Personal Care & Hygiene",
    filter_devices: "Medical Devices & Equipment",

    // Sort Dropdown
    sort_relevance: "Sort: Most Relevant",
    sort_name_asc: "Name (A - Z)",
    sort_price_asc: "Price: Low to High",
    sort_price_desc: "Price: High to Low",

    // Checkboxes
    filter_pediatric: "Pediatric Approved",
    filter_pregnancy: "Pregnancy Safe",

    // About Page
    about_title: "About Dawaa'i AI Healthcare Platform",
    about_subtitle: "Leading digital platform simplifying medical leaflets and healthcare insights in Arabic & English.",
    about_sec1_title: "Clinical Vision & Mission",
    about_sec1_desc: "Dawaa'i AI empowers patients and healthcare professionals with swift, verified access to registered medication data, translating complex medical jargon into clear, safe explanations that support informed decisions without compromising safety.",
    about_sec2_title: "Data Integrity & Scientific Transparency",
    about_sec2_desc: "The platform builds directly upon official regulatory registries from the Egyptian Drug Authority (EDA), Saudi SFDA, US FDA, and European EMA. Our system never invents or hallucinates clinical claims beyond verified sources.",
    about_sec3_title: "Patient Privacy & Security",
    about_sec3_desc: "We adhere to the highest digital health privacy standards. We never sell patient search habits, and public testimonials are sanitized to safeguard user anonymity.",

    // Legal & Privacy Modals
    privacy_title: "Privacy Policy & Data Protection",
    privacy_p1: "Dawaa'i AI respects the privacy of all visitors and users. We do not harvest, sell, or share personal medical records, nor do we correlate search habits with real-world identities.",
    privacy_p2: "User login sessions are used strictly to provide personalized preferences and language settings. Public user reviews are completely anonymized upon publication to safeguard patient confidentiality.",
    terms_title: "Terms of Service & Clinical Scope",
    terms_p1: "Dawaa'i AI is an educational digital service designed to facilitate understanding of authorized medication leaflets. The information provided does not constitute human medical advice or diagnosis. Patients must never discontinue or alter prescribed treatments without consulting a licensed physician.",
    disclaimer_title: "Explicit Clinical Disclaimer",
    modal_close: "Close",

    // Call to Action
    cta_title: "Start Checking Your Medicines with Absolute Precision",
    cta_desc: "Search by brand name, easily read clinical leaflets, or consult the AI assistant anytime.",
    cta_btn_search: "Search Medicines Now",
    cta_btn_assistant: "Chat with AI Assistant",

    // Search Category Options
    cat_opt_analgesics: "Analgesics & Antipyretics",
    cat_opt_antibiotics: "Antibiotics",
    cat_opt_nsaids: "Anti-Inflammatory Drugs",
    cat_opt_diabetes: "Diabetes Medications",
    cat_opt_gi: "Antacids & Acid Reducers",
    cat_opt_cholesterol: "Cholesterol & Lipid Reducers",
    cat_opt_allergy: "Antihistamines & Allergy",
    cat_opt_respiratory: "Bronchodilators & Asthma",

    // Scan Page
    scan_formats_supported: "Supports JPG, PNG, and WEBP for any medicine worldwide",
    scan_auto_detect_badge: "📸 Automated AI Identification & Analysis",
    scan_btn_choose_other: "Choose Another Image",
    scan_sample_pill_title: "Instant One-Click Clinical Test Samples",
    scan_sample_omeprazole: "💊 Omeprazole 20 mg (Antacid & Ulcer)",
    scan_loading_main: "Analyzing packaging with AI & extracting accurate clinical data...",
    scan_loading_sub: "Extracting text, verifying registries, and matching FDA/EMA safety criteria...",

    // Interactions
    inter_quick_combos_heading: "⚡ Common Clinical Combinations for Quick Check:",
    combo_plavix_omeprazole: "⛔ Plavix + Omeprazole",
    combo_lipitor_klacid: "⚠️ Lipitor + Klacid",
    inter_lbl_med1: "First Medicine (Brand or Generic):",
    inter_lbl_med2: "Second Medicine (Brand or Generic):",
    inter_btn_check: "Check Drug Interaction Now",

    // Chat / Assistant
    chat_welcome_title: "Welcome to Dawaa'i AI 👋",
    chat_welcome_desc: "I am your intelligent medical assistant. Ask me about medicine indications, dosages, side effects, or drug interactions.",
    chat_prompt_headache: "I have a severe headache, what should I take?",
    chat_prompt_gerd: "Remedy for heartburn and acid reflux",
    chat_prompt_cramps: "Treatment for abdominal cramps and spasms",
    chat_prompt_cough: "Remedy for cough and phlegm",
    chat_prompt_cold: "Treatment for flu, runny nose, and cold",
    chat_badge_official: "✓ Grounded Official Authorities",
    chat_badge_privacy: "✓ Encrypted Medical Privacy",
    chat_badge_bilingual: "✓ Full Bilingual Support (AR / EN)",

    // History Filters
    history_filter_all: "🌐 All Activities",
    history_filter_searches: "🔍 Searches",
    history_filter_views: "💊 Viewed Medicines",
    history_filter_scans: "📷 Scanned Packs",
    history_filter_assistant: "🤖 AI Consultations",
    history_loading_text: "Loading your medical activity history...",

    // Admin
    admin_btn_refresh: "🔄 Refresh Metrics",
    admin_health_checking: "Checking server response and AI model availability...",
    admin_reviews_subtitle: "Review and approve user feedback while maintaining statistical integrity of digital ratings.",
    th_user: "User",
    th_rating: "Rating",
    th_comment: "Review",
    th_category: "Category",
    th_status: "Status",
    th_action: "Action",

    // Footer
    footer_link_registry: "Approved Medicines Registry",
    footer_rights: ". All rights reserved.",
    footer_tagline: "Understand Your Medicine, with Confidence.",

    footer_copyright: "© {year} Dawaa'i AI. All rights reserved."
  }
};

let currentLanguage = localStorage.getItem("dawaai_lang") || "ar";

function getLanguage() {
  return currentLanguage;
}

function setLanguage(lang) {
  if (lang !== "ar" && lang !== "en") return;
  currentLanguage = lang;
  localStorage.setItem("dawaai_lang", lang);
  
  // Set HTML attributes
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  
  // Dispatch event for UI updates
  window.dispatchEvent(new CustomEvent("languageChanged", { detail: { lang } }));
  updatePageTranslations();
}

function t(key, params = {}, fallback = "") {
  if (!key) return "";
  const dict = (typeof translations !== "undefined" && translations[currentLanguage]) || (typeof translations !== "undefined" && translations["ar"]) || {};
  const enDict = (typeof translations !== "undefined" && translations["en"]) || {};
  let str = dict[key] !== undefined ? dict[key] : (enDict[key] !== undefined ? enDict[key] : fallback);
  
  if (str === null || str === undefined || str === "") {
    // Strictly prevent displaying raw code keys in the UI
    return "";
  }
  
  // Replace parameters like {year} or {count}
  for (const [k, v] of Object.entries(params)) {
    str = String(str).replace(new RegExp(`\\{${k}\\}`, "g"), v);
  }
  return str;
}

function updatePageTranslations() {
  const isAr = currentLanguage === "ar";

  // Update Page Title and Meta Description
  document.title = isAr 
    ? "دوائي AI — افهم دواءك بثقة | Dawaa'i AI" 
    : "Dawaa'i AI — Understand Your Medicine with Confidence";

  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) {
    metaDesc.setAttribute("content", isAr
      ? "منصة ذكية موثوقة لمعلومات الأدوية، قراءة النشرات الطبية، وتبسيط المصطلحات باللغتين العربية والإنجليزية استناداً لمراجع هيئات الغذاء والدواء."
      : "Verified intelligent platform for medicine information, patient leaflet reading, and clinical terminology simplification grounded in official FDA & health authority monographs."
    );
  }

  // Update Segmented Control Active State
  document.querySelectorAll("#btn-lang-ar, #btn-mobile-lang-ar").forEach(b => {
    if (isAr) b.classList.add("active"); else b.classList.remove("active");
  });
  document.querySelectorAll("#btn-lang-en, #btn-mobile-lang-en").forEach(b => {
    if (!isAr) b.classList.add("active"); else b.classList.remove("active");
  });

  // Translate all [data-i18n]
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (key) {
      const translated = t(key);
      if (translated) {
        if (translated.includes("<") && translated.includes(">")) {
          el.innerHTML = translated;
        } else {
          el.textContent = translated;
        }
      }
    }
  });

  // Translate [data-i18n-html]
  document.querySelectorAll("[data-i18n-html]").forEach(el => {
    const key = el.getAttribute("data-i18n-html");
    if (key) {
      const translated = t(key);
      if (translated) {
        el.innerHTML = translated;
      }
    }
  });

  // Translate placeholders
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (key) {
      const translated = t(key);
      if (translated) {
        el.setAttribute("placeholder", translated);
      }
    }
  });

  // Translate titles
  document.querySelectorAll("[data-i18n-title]").forEach(el => {
    const key = el.getAttribute("data-i18n-title");
    if (key) {
      const translated = t(key);
      if (translated) {
        el.setAttribute("title", translated);
      }
    }
  });

  // Translate <select> options with data-i18n
  document.querySelectorAll("option[data-i18n]").forEach(opt => {
    const key = opt.getAttribute("data-i18n");
    if (key) {
      const translated = t(key);
      if (translated) {
        opt.textContent = translated;
      }
    }
  });

  // Update current year
  document.querySelectorAll(".current-year").forEach(el => {
    el.textContent = new Date().getFullYear();
  });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  setLanguage(currentLanguage);
});
