import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CandidateProfileView } from "../src/components/candidate-screen";
import type { CandidateProfile } from "../src/types";

const profile: CandidateProfile = {
  id: "candidate", user_id: "user", first_name: "Мария", last_name: "Смирнова",
  city: "Москва", about: "Backend-разработчик", specialization: "BACKEND",
  declared_grade: "SENIOR", verified_grade: "MIDDLE", normalized_assessment_score: 90,
  assessment_verified_at: "2026-10-05T12:00:00Z", years_of_experience: 3,
  fsp_id: null, personal_data_consent: true, personal_data_consent_at: "2026-10-05T12:00:00Z",
  skills: [{ id: "python", name: "Python" }],
};
function view(overrides: Partial<CandidateProfile> = {}) {
  return renderToStaticMarkup(createElement(CandidateProfileView, { profile: { ...profile, ...overrides } }));
}
function text(html: string) { return html.replace(/<[^>]*>/g, "").replace(/\s+/g, " "); }

test("candidate separates canonical qualification from declared grade and skills", () => {
  const html = view();
  assert.match(html, /<h1>Мария Смирнова<\/h1>/);
  assert.match(html, /aria-label="Квалификация"[\s\S]*Подтверждена тестированием/);
  assert.match(text(html), /Подтверждённый уровеньMiddleРезультат тестирования90 \/ 100/);
  assert.match(html, /aria-label="Самостоятельно указанные навыки"/);
  assert.match(html, /Указаны кандидатом/);
  assert.match(html, /<li>Python<\/li>/);
  assert.match(html, /Заявленный уровень<\/dt><dd>Senior/);
  assert.doesNotMatch(html, /Подтверждённые навыки|Подтверждённый опыт/);
  for (const path of ["/candidate/edit", "/candidate/assessment"])
    assert.ok(html.includes('href="' + path + '"'));
  assert.doesNotMatch(html, /href="\/candidate\/invitations"/);
  assert.match(html, /MOCK \/ прототип/);
});
test("candidate assessment CTA reflects verification and keeps the existing assessment route", () => {
  const verified = view();
  assert.match(verified, /href="\/candidate\/assessment">\s*Результаты тестирования\s*<\/a>/);
  assert.doesNotMatch(verified, /Подтвердить уровень|Подтверждена assessment/);
  const unverified = view({ verified_grade: null, normalized_assessment_score: null, assessment_verified_at: null });
  assert.match(unverified, /href="\/candidate\/assessment">\s*Подтвердить уровень\s*<\/a>/);
  assert.doesNotMatch(unverified, /Результаты тестирования/);
});
test("candidate canonical unverified and empty optional fields do not fabricate evidence", () => {
  const html = view({
    verified_grade: null, normalized_assessment_score: null, assessment_verified_at: null,
    skills: [], city: null, about: null, years_of_experience: null, personal_data_consent: false,
  });
  assert.match(html, /Пока не подтверждена/);
  assert.match(html, /Навыки не указаны/);
  assert.match(html, /Информация о себе не указана/);
  assert.match(html, /Город<\/dt><dd>Не указан/);
  assert.match(html, /Опыт, лет<\/dt><dd>Не указан/);
  assert.match(html, /Согласие на обработку данных<\/dt><dd>Не дано/);
  assert.doesNotMatch(html, /Подтверждена тестированием|NaN|Invalid Date|undefined/);
});
test("candidate keeps legitimate zero assessment and experience and escapes user content", () => {
  const html = view({
    normalized_assessment_score: 0, years_of_experience: 0, about: "<script>private()</script>",
    skills: [{ id: "unsafe", name: "<b>Skill</b>" }],
  });
  assert.match(text(html), /Результат тестирования0 \/ 100/);
  assert.match(html, /Опыт, лет<\/dt><dd>0<\/dd>/);
  assert.match(html, /&lt;script&gt;private/);
  assert.match(html, /&lt;b&gt;Skill/);
  assert.doesNotMatch(html, /<script>|<b>Skill/);
});
test("official logos and fonts keep source bytes and licenses retain normalized source text", () => {
  const hashes: Record<string, string> = {
    "public/brand/fsp-full-dark.svg": "3e38c1488ec8345eb37bcaa0c807695e9446c881aaa7ceb6a693761493dd3045",
    "public/brand/fsp-compact-dark.svg": "d92d7e94f4b43eb55e9e8d4fa33b958698b91e4ad48d2b311324765b4eee429f",
    "src/fonts/JetBrainsMono-Regular.ttf": "b6b1ff4ddefe36d7f2a6174e1d001cab374e594519ee9049af028d577b64c5f5",
    "src/fonts/JetBrainsMono-Bold.ttf": "a2349098b9e45419e7bf0e2958d6c4937a049dded37387b08be725be4c7615f3",
    "src/fonts/TDAText.ttf": "555e8554d2a97c02dfbde4758f4901592ae2b2cf7c42d1abb317a7b29ce50e3e",
    // License copies normalize CRLF/trailing whitespace only, preserving legal text.
    "public/brand/licenses/JetBrainsMono-OFL.txt": "c1ab7c666206842a02b35b30770dac0d7a10156ed401c9defc3f02a754d89e90",
    "public/brand/licenses/TDAText-LICENSE.txt": "fe4ddef88d2705569740a4b6c59e1a73315e1a55fb0a0d054bd791977681f8cb",
    "public/brand/licenses/TDAText-COPYRIGHT.txt": "48bfd68573006676daa46714496f979bdcc856fd5e96acdee65b4dd7aaa77637",
  };
  for (const [path, expected] of Object.entries(hashes))
    assert.equal(createHash("sha256").update(readFileSync(path)).digest("hex"), expected, path);
  const layout = readFileSync("src/app/layout.tsx", "utf8");
  assert.match(layout, /next\/font\/local/);
  assert.doesNotMatch(layout, /next\/font\/google|fonts\.googleapis/);
  assert.match(layout, /href="#main-content"/);
  assert.match(layout, /id="main-content"/);
});
test("brand palette and semantic feedback have readable text contrast", () => {
  const css = readFileSync("src/app/globals.css", "utf8");
  for (const color of ["402fff", "0a006b", "ec1d35", "1b1c21", "2d2e37", "3a3c46", "9b9c9e", "d9d9d9", "ededed"])
    assert.ok(css.toLowerCase().includes("#" + color));
  function luminance(hex: string) {
    const rgb = hex.match(/.{2}/g)!.map(part => parseInt(part, 16) / 255)
      .map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  }
  function token(name: string) {
    const value = css.match(new RegExp("--" + name + ": #([0-9a-f]{6});", "i"))?.[1];
    assert.ok(value, name); return value;
  }
  for (const [foreground, background] of [
    ["brand-blue", "color-surface"], ["brand-secondary", "brand-light"],
    ["color-success", "color-success-soft"], ["color-error", "color-error-soft"],
    ["color-warning", "color-warning-soft"],
  ]) {
    const a = luminance(token(foreground)), b = luminance(token(background));
    assert.ok((Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05) >= 4.5, foreground);
  }
});
