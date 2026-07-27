import Image from "next/image";

const groups = [
  {
    years: "5–7",
    title: "Первые шаги",
    text: "Баланс, координация и любовь ко льду через игру.",
    tag: "Старт",
  },
  {
    years: "8–10",
    title: "Младшая стая",
    text: "Техника катания, владение клюшкой и командное мышление.",
    tag: "База",
  },
  {
    years: "11–14",
    title: "Волчья лига",
    text: "Тактика, характер и подготовка к городским турнирам.",
    tag: "Про",
  },
];

const principles = [
  ["01", "Характер", "Учимся отвечать за себя, партнёров и результат."],
  ["02", "Мастерство", "Отрабатываем технику осознанно — от шага к шагу."],
  ["03", "Команда", "На льду нет чужих: растём, побеждаем и ошибаемся вместе."],
  ["04", "Безопасность", "Возрастные нагрузки, защитная экипировка и внимание тренера."],
];

const schedule = [
  ["ПН", "17:30", "Лёд", "Академия спорта"],
  ["СР", "18:15", "Лёд + ОФП", "Академия спорта"],
  ["СБ", "10:00", "Командная", "Хоккейный город"],
];

export default function Home() {
  return (
    <main>
      <header className="siteHeader">
        <a className="brand" href="#top" aria-label="Inkerin Sudet — на главную">
          <span className="brandMark">IS</span>
          <span className="brandText">
            <strong>INKERIN SUDET</strong>
            <small>Санкт-Петербург · 2026</small>
          </span>
        </a>
        <nav aria-label="Основная навигация">
          <a href="#about">О клубе</a>
          <a href="#groups">Команды</a>
          <a href="#schedule">Расписание</a>
        </nav>
        <a className="headerCta" href="#trial">
          Пробная тренировка <span>↗</span>
        </a>
      </header>

      <section className="hero" id="top">
        <div className="heroLines" aria-hidden="true" />
        <div className="heroContent">
          <p className="eyebrow"><span>Детский хоккейный клуб</span> Санкт-Петербург</p>
          <h1>
            РАСТИ
            <span>В СТАЕ.</span>
          </h1>
          <p className="heroLead">
            Воспитываем сильных игроков и надёжных товарищей.
            Для детей от 5 до 14 лет — с нуля до первой лиги.
          </p>
          <div className="heroActions">
            <a className="primaryButton" href="#trial">Записаться на лёд <span>→</span></a>
            <a className="textLink" href="#about">Узнать о клубе <span>↓</span></a>
          </div>
          <div className="heroStats" aria-label="Показатели клуба">
            <div><strong>120+</strong><span>юных игроков</span></div>
            <div><strong>7</strong><span>тренеров</span></div>
            <div><strong>3</strong><span>возрастные группы</span></div>
          </div>
        </div>

        <div className="heroVisual" aria-label="Эмблема хоккейного клуба Inkerin Sudet">
          <div className="crestHalo" />
          <Image
            src="/brand/crest-blue.png"
            alt="Волк на эмблеме хоккейного клуба Inkerin Sudet"
            width={1254}
            height={1254}
            priority
            className="heroCrest"
          />
          <div className="heroBadge">
            <span>05</span>
            <strong>ПЕРВЫЙ ВЫХОД<br />НА ЛЁД</strong>
            <i>лет</i>
          </div>
          <p className="visualCaption">Храбрость в сердце.<br />Холод в голове.</p>
        </div>
        <div className="heroTicker">
          <span>INKERIN SUDET</span><i>◆</i><span>ДИСЦИПЛИНА</span><i>◆</i>
          <span>СКОРОСТЬ</span><i>◆</i><span>КОМАНДА</span><i>◆</i>
          <span>САНКТ-ПЕТЕРБУРГ</span>
        </div>
      </section>

      <section className="manifesto" id="about">
        <div className="sectionIndex">/ 01</div>
        <div className="manifestoTitle">
          <p className="eyebrow dark">Философия стаи</p>
          <h2>НЕ ПРОСТО<br /><span>ИГРА.</span></h2>
        </div>
        <div className="manifestoCopy">
          <p className="leadQuote">
            Хоккей учит падать, вставать и снова идти вперёд —
            рядом с теми, кому доверяешь.
          </p>
          <p>
            «Ингерманландские волки» — вымышленный клуб с настоящими
            ценностями. Здесь результат важен, но ещё важнее путь:
            уважение, дисциплина, поддержка и радость от каждого выхода на лёд.
          </p>
          <div className="signature">Sudet · одна стая</div>
        </div>
      </section>

      <section className="principlesSection">
        <div className="principlesGrid">
          {principles.map(([number, title, text]) => (
            <article className="principleCard" key={number}>
              <span>{number}</span>
              <div className="principleIcon" aria-hidden="true">✦</div>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="groupsSection" id="groups">
        <div className="sectionHead">
          <div>
            <p className="eyebrow">Команды клуба</p>
            <h2>НАЙДИ СВОЮ<br /><span>СТАЮ</span></h2>
          </div>
          <p>
            Группы формируются по возрасту и уровню подготовки.
            Перед стартом тренер проводит короткое знакомство на льду.
          </p>
        </div>
        <div className="groupsGrid">
          {groups.map((group, index) => (
            <article className={`groupCard groupCard${index + 1}`} key={group.years}>
              <div className="cardTop">
                <span>{group.tag}</span>
                <i>0{index + 1}</i>
              </div>
              <div className="age"><strong>{group.years}</strong><small>лет</small></div>
              <div className="cardBottom">
                <h3>{group.title}</h3>
                <p>{group.text}</p>
                <a href="#trial" aria-label={`Записаться в группу ${group.title}`}>Подробнее <span>↗</span></a>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="kitSection">
        <div className="kitImage">
          <Image
            src="/brand/embroidery.png"
            alt="Вышитая эмблема Inkerin Sudet на чёрной форме"
            width={1254}
            height={1254}
          />
          <span className="kitTag">CLUB ID · 2026</span>
        </div>
        <div className="kitContent">
          <p className="eyebrow">Свои цвета. Своя история.</p>
          <h2>ФОРМА, КОТОРУЮ<br /><span>НОСЯТ С ГОРДОСТЬЮ</span></h2>
          <p>
            Чёрный — собранность. Серебро — лёд Петербурга.
            Янтарный — огонь, который каждый игрок приносит в команду.
          </p>
          <div className="colorRow" aria-label="Цвета клуба">
            <span className="swatch black">Ночь</span>
            <span className="swatch blue">Лёд</span>
            <span className="swatch gold">Янтарь</span>
          </div>
          <blockquote>«Эмблема на груди — обещание команде»</blockquote>
        </div>
      </section>

      <section className="scheduleSection" id="schedule">
        <div className="scheduleIntro">
          <div className="sectionIndex light">/ 04</div>
          <p className="eyebrow">Неделя младшей стаи · 8–10 лет</p>
          <h2>ТРИ ВСТРЕЧИ.<br /><span>ОДНА ЦЕЛЬ.</span></h2>
          <p>Пробное занятие проходит по средам. Экипировку для первого выхода поможем подобрать.</p>
        </div>
        <div className="scheduleList">
          {schedule.map(([day, time, type, place]) => (
            <div className="scheduleRow" key={day}>
              <strong>{day}</strong>
              <time>{time}</time>
              <span>{type}</span>
              <small>{place}</small>
            </div>
          ))}
        </div>
      </section>

      <section className="trialSection" id="trial">
        <div className="trialKicker">ПЕРВЫЙ ШАГ В БОЛЬШУЮ ИГРУ</div>
        <div className="trialGrid">
          <div>
            <p className="eyebrow dark">Бесплатная пробная тренировка</p>
            <h2>ВЫХОДИ<br />НА <span>ЛЁД.</span></h2>
          </div>
          <div className="trialCopy">
            <p>
              Оставьте контакты — администратор подберёт группу,
              расскажет об экипировке и договорится о дате знакомства.
            </p>
            <form className="trialForm" action="mailto:hello@inkerinsudet.ru" method="post" encType="text/plain">
              <label>
                <span>Имя родителя</span>
                <input name="name" type="text" placeholder="Как к вам обращаться" required />
              </label>
              <label>
                <span>Телефон</span>
                <input name="phone" type="tel" placeholder="+7 (___) ___-__-__" required />
              </label>
              <label>
                <span>Возраст ребёнка</span>
                <input name="age" type="number" min="5" max="14" placeholder="8 лет" required />
              </label>
              <button type="submit">Записаться в стаю <span>→</span></button>
            </form>
            <small className="formNote">Нажимая кнопку, вы соглашаетесь на обработку данных.</small>
          </div>
        </div>
      </section>

      <footer>
        <div className="footerBrand">
          <span className="brandMark">IS</span>
          <div><strong>INKERIN SUDET</strong><small>Ингерманландские волки</small></div>
        </div>
        <div className="footerContact">
          <span>Санкт-Петербург</span>
          <a href="mailto:hello@inkerinsudet.ru">hello@inkerinsudet.ru</a>
          <a href="tel:+78125550126">+7 812 555-01-26</a>
        </div>
        <div className="footerMeta">
          <span>Вымышленный клуб · Портфолио</span>
          <span>Идея, логотипы и сайт принадлежат Яну Ковру</span>
          <span>© 2026 Ян Ковру · Все права защищены</span>
        </div>
      </footer>
    </main>
  );
}
