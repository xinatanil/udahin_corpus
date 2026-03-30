#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelinePaths:
    input_dict: str = '../../sources/corrected_source_dict.xml'
    converted_dict: str = '../output/converted_dict.xml'
    fixed_source: str = '../output/corrected_source_fixed.xml'
    colon_candidates_report: str = '../output/colon_candidates.txt'
    colon_candidates_tsv: str = '../output/colon_candidates.tsv'
    suspicious_links_report: str = '../output/suspicious_links.txt'
    suspicious_links_tsv: str = '../output/suspicious_links.tsv'


class PipelineRunner:
    def __init__(self) -> None:
        self.script_dir = Path(__file__).resolve().parent
        self.root_dir = self.script_dir.parent
        self.paths = PipelinePaths()

    def abs_path(self, relative: str) -> Path:
        return (self.script_dir / relative).resolve()

    def run_command(self, *cmd: str, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(cmd),
            cwd=self.script_dir,
            env=env,
            check=check,
            text=True,
            capture_output=False,
        )

    def run_python(self, script_name: str, *args: str) -> None:
        self.run_command('python3', script_name, *args)

    def run_bash(self, script_name: str, *args: str) -> None:
        self.run_command('bash', script_name, *args)

    def run_saxon(self, xsl_name: str, source: str, output: str) -> None:
        self.run_command(
            'saxon',
            f'-xsl:{xsl_name}',
            f'-s:{source}',
            f'-o:{output}',
        )

    def notify_done(self, message: str) -> None:
        if os.environ.get('PIPELINE_V2_NO_NOTIFY', '0') == '1':
            return
        if shutil.which('osascript'):
            subprocess.run(
                [
                    'osascript',
                    '-e',
                    f'display notification "{message}" with title "convert_source_dict_v2.sh"',
                ],
                check=False,
                text=True,
            )
        else:
            sys.stdout.write('\a')
            sys.stdout.flush()

    def lint(self, relative_file: str) -> None:
        target = self.abs_path(relative_file)
        fd, temp_name = tempfile.mkstemp(dir=str(target.parent))
        os.close(fd)
        temp_path = Path(temp_name)
        env = os.environ.copy()
        env['XMLLINT_INDENT'] = '\t'
        try:
            subprocess.run(
                ['xmllint', '--format', relative_file, '--output', str(temp_path)],
                cwd=self.script_dir,
                env=env,
                check=True,
                text=True,
                capture_output=False,
            )
            temp_path.replace(target)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    def copy_previous_output(self) -> None:
        converted = self.abs_path(self.paths.converted_dict)
        old_path = Path(f'{converted}.old')
        if converted.exists():
            shutil.copy2(converted, old_path)

    def write_diff(self) -> None:
        converted = self.paths.converted_dict
        old_converted = f'{converted}.old'
        old_path = self.abs_path(old_converted)
        diff_path = self.abs_path(f'{converted}.diff')
        if not old_path.exists():
            return

        print('Generating diff...')
        result = subprocess.run(
            ['diff', '-u', old_converted, converted],
            cwd=self.script_dir,
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode not in {0, 1}:
            raise subprocess.CalledProcessError(
                result.returncode,
                result.args,
                output=result.stdout,
                stderr=result.stderr,
            )
        diff_path.write_text(result.stdout, encoding='utf-8')
        print(f'Diff saved to {converted}.diff')

    def replace_in_file(self, relative_file: str, old: str, new: str) -> None:
        target = self.abs_path(relative_file)
        content = target.read_text(encoding='utf-8')
        content = content.replace(old, new)
        target.write_text(content, encoding='utf-8')

    def remove_empty_blockquotes(self, relative_file: str) -> None:
        self.replace_in_file(relative_file, '<blockquote/>', '')
        self.replace_in_file(relative_file, '<blockquote />', '')
        self.replace_in_file(relative_file, '--------', '')

    def stage(self, name: str, func) -> None:
        started = time.monotonic()
        print(f'[{name}]')
        func()
        elapsed = time.monotonic() - started
        print(f'[{name}] done in {elapsed:.2f}s')

    def run(self) -> None:
        p = self.paths
        self.copy_previous_output()

        self.stage('source_fixes', lambda: self.run_python('apply_source_fixes.py', p.input_dict, p.fixed_source))
        self.stage('sorting_xsl', lambda: self.run_saxon('sorting_xsl_template.xsl', p.fixed_source, p.converted_dict))
        self.stage('identify_glued_cards', lambda: self.run_python('identify_glued_cards.py', p.converted_dict, p.converted_dict))

        def fix_homonyms() -> None:
            fd, temp_name = tempfile.mkstemp(dir=str(self.abs_path('../output')))
            os.close(fd)
            temp_rel = os.path.relpath(temp_name, self.script_dir)
            try:
                self.run_saxon('fix_homonyms.xsl', p.converted_dict, temp_rel)
                Path(temp_name).replace(self.abs_path(p.converted_dict))
            finally:
                Path(temp_name).unlink(missing_ok=True)
            self.replace_in_file(p.converted_dict, 'openingCardTag', '<card>')
            self.replace_in_file(p.converted_dict, 'closingCardTag', '</card>')

        self.stage('fix_homonyms', fix_homonyms)
        self.stage('lint_after_fix_homonyms', lambda: self.lint(p.converted_dict))

        def fix_lexical_meanings() -> None:
            fd, temp_name = tempfile.mkstemp(dir=str(self.abs_path('../output')))
            os.close(fd)
            temp_rel = os.path.relpath(temp_name, self.script_dir)
            try:
                self.run_saxon('fix_lexical_meanings.xsl', p.converted_dict, temp_rel)
                Path(temp_name).replace(self.abs_path(p.converted_dict))
            finally:
                Path(temp_name).unlink(missing_ok=True)
            self.replace_in_file(p.converted_dict, 'openingMeaningTag', '<meaning>')
            self.replace_in_file(p.converted_dict, 'closingMeaningTag', '</meaning>')

        self.stage('fix_lexical_meanings', fix_lexical_meanings)
        self.stage('lint_after_fix_lexical_meanings', lambda: self.lint(p.converted_dict))
        self.stage('format_numbered_meanings', lambda: self.run_python('format_numbered_meanings.py', p.converted_dict, p.converted_dict))
        self.stage('lint_after_format_numbered_meanings', lambda: self.lint(p.converted_dict))

        self.stage('apply_tree_stage', lambda: self.run_python('apply_tree_stage.py', p.converted_dict, p.converted_dict))
        self.stage('apply_pre_links_xr_stage', lambda: self.run_python('apply_pre_links_xr_stage.py', p.converted_dict, p.converted_dict))
        self.stage('identify_links', lambda: self.run_python('identify_links.py', p.converted_dict, p.converted_dict))
        self.stage('apply_post_links_tree_stage', lambda: self.run_python('apply_post_links_tree_stage.py', p.converted_dict, p.converted_dict))
        self.stage('apply_semantic_stage', lambda: self.run_python('apply_semantic_stage.py', p.converted_dict, p.converted_dict))
        self.stage('identify_examples', lambda: self.run_python('identify_examples.py', p.converted_dict, p.converted_dict))
        self.stage('lint_after_semantics', lambda: self.lint(p.converted_dict))

        self.stage('cleanup_empty_blockquotes', lambda: self.remove_empty_blockquotes(p.converted_dict))
        self.stage('lint_after_cleanup', lambda: self.lint(p.converted_dict))

        self.stage('compile_homonyms', lambda: self.run_python('compile_homonyms.py', p.converted_dict, p.converted_dict))
        self.stage('lint_after_compile_homonyms', lambda: self.lint(p.converted_dict))
        self.stage('apply_post_fixes', lambda: self.run_python('apply_post_fixes.py', p.converted_dict, p.converted_dict))
        self.stage('lint_after_post_fixes', lambda: self.lint(p.converted_dict))
        self.stage('apply_colon_rules', lambda: self.run_python('apply_colon_rules.py', p.converted_dict, p.converted_dict))
        self.stage('lint_after_colon_rules', lambda: self.lint(p.converted_dict))

        self.stage('calculate_tag_counts', lambda: self.run_bash('calculate_tag_counts.sh', p.converted_dict))
        self.stage('list_keyword_blockquotes', lambda: self.run_python('list_keyword_blockquotes.py', p.converted_dict, '../output/keyword_blockquotes_no_colon.txt'))
        self.stage('report_colon_candidates', lambda: self.run_python('report_colon_candidates.py', p.converted_dict, p.colon_candidates_report, p.colon_candidates_tsv))
        self.stage('report_suspicious_links', lambda: self.run_python('report_suspicious_links.py', p.converted_dict, p.suspicious_links_report, p.suspicious_links_tsv))

        self.write_diff()
        self.notify_done('Finished processing converted_dict.xml')


def main() -> int:
    runner = PipelineRunner()
    runner.run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
