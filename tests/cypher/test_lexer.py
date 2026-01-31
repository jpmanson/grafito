"""Tests for the Cypher lexer."""

import pytest
from grafito.cypher.lexer import Lexer
from grafito.cypher.tokens import Token, TokenType
from grafito.cypher.exceptions import CypherSyntaxError


class TestLexerKeywords:
    """Test tokenization of keywords."""

    def test_tokenize_create(self):
        lexer = Lexer("CREATE")
        tokens = lexer.tokenize()
        assert len(tokens) == 2  # CREATE + EOF
        assert tokens[0].type == TokenType.CREATE
        assert tokens[1].type == TokenType.EOF

    def test_tokenize_match(self):
        lexer = Lexer("MATCH")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MATCH

    def test_tokenize_where(self):
        lexer = Lexer("WHERE")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.WHERE

    def test_tokenize_return(self):
        lexer = Lexer("RETURN")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.RETURN

    def test_tokenize_and_or_not(self):
        lexer = Lexer("AND OR NOT")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.AND
        assert tokens[1].type == TokenType.OR
        assert tokens[2].type == TokenType.NOT

    def test_tokenize_call(self):
        lexer = Lexer("CALL")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.CALL

    def test_tokenize_in(self):
        lexer = Lexer("IN")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IN

    def test_tokenize_predicates(self):
        lexer = Lexer("ANY ALL NONE SINGLE")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.ANY
        assert tokens[1].type == TokenType.ALL
        assert tokens[2].type == TokenType.NONE
        assert tokens[3].type == TokenType.SINGLE

    def test_tokenize_case_keywords(self):
        lexer = Lexer("CASE WHEN THEN ELSE END")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.CASE
        assert tokens[1].type == TokenType.WHEN
        assert tokens[2].type == TokenType.THEN
        assert tokens[3].type == TokenType.ELSE
        assert tokens[4].type == TokenType.END

    def test_keywords_case_insensitive(self):
        lexer = Lexer("match MaTcH MATCH")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MATCH
        assert tokens[1].type == TokenType.MATCH
        assert tokens[2].type == TokenType.MATCH


class TestLexerLiterals:
    """Test tokenization of literals."""

    def test_tokenize_identifier(self):
        lexer = Lexer("n person_name _var")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "n"
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "person_name"
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "_var"

    def test_tokenize_integer(self):
        lexer = Lexer("42 0 123")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == 42
        assert tokens[1].type == TokenType.INTEGER
        assert tokens[1].value == 0
        assert tokens[2].type == TokenType.INTEGER
        assert tokens[2].value == 123

    def test_tokenize_float(self):
        lexer = Lexer("3.14 0.5 100.0")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.FLOAT
        assert tokens[0].value == 3.14
        assert tokens[1].type == TokenType.FLOAT
        assert tokens[1].value == 0.5
        assert tokens[2].type == TokenType.FLOAT
        assert tokens[2].value == 100.0

    def test_tokenize_string_double_quotes(self):
        lexer = Lexer('"hello world"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello world"

    def test_tokenize_string_single_quotes(self):
        lexer = Lexer("'Alice'")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "Alice"

    def test_tokenize_string_with_escapes(self):
        lexer = Lexer(r'"Hello\nWorld\tTest"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "Hello\nWorld\tTest"

    def test_tokenize_boolean_true(self):
        lexer = Lexer("true TRUE True")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.BOOLEAN
        assert tokens[0].value is True
        assert tokens[1].type == TokenType.BOOLEAN
        assert tokens[1].value is True

    def test_tokenize_boolean_false(self):
        lexer = Lexer("false FALSE False")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.BOOLEAN
        assert tokens[0].value is False
        assert tokens[1].type == TokenType.BOOLEAN
        assert tokens[1].value is False

    def test_tokenize_null(self):
        lexer = Lexer("null NULL")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NULL
        assert tokens[0].value is None
        assert tokens[1].type == TokenType.NULL
        assert tokens[1].value is None


class TestLexerSymbols:
    """Test tokenization of symbols and operators."""

    def test_tokenize_parentheses(self):
        lexer = Lexer("()")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].type == TokenType.RPAREN

    def test_tokenize_braces(self):
        lexer = Lexer("{}")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LBRACE
        assert tokens[1].type == TokenType.RBRACE

    def test_tokenize_brackets(self):
        lexer = Lexer("[]")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.LBRACKET
        assert tokens[1].type == TokenType.RBRACKET

    def test_tokenize_colon_comma_dot(self):
        lexer = Lexer(":,.")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.COLON
        assert tokens[1].type == TokenType.COMMA
        assert tokens[2].type == TokenType.DOT

    def test_tokenize_pipe(self):
        lexer = Lexer("|")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PIPE

    def test_tokenize_plus(self):
        lexer = Lexer("+")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.PLUS

    def test_tokenize_arrow_right(self):
        lexer = Lexer("->")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.ARROW_RIGHT
        assert tokens[0].value == "->"

    def test_tokenize_arrow_left(self):
        lexer = Lexer("<-")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.ARROW_LEFT
        assert tokens[0].value == "<-"

    def test_tokenize_dash(self):
        lexer = Lexer("-")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.DASH
        assert tokens[0].value == "-"

    def test_tokenize_comparison_operators(self):
        lexer = Lexer("= != < > <= >=")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.EQ
        assert tokens[1].type == TokenType.NEQ
        assert tokens[2].type == TokenType.LT
        assert tokens[3].type == TokenType.GT
        assert tokens[4].type == TokenType.LTE
        assert tokens[5].type == TokenType.GTE


class TestLexerComplexQueries:
    """Test tokenization of complete queries."""

    def test_tokenize_simple_create(self):
        lexer = Lexer("CREATE (n:Person)")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.CREATE
        assert tokens[1].type == TokenType.LPAREN
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "n"
        assert tokens[3].type == TokenType.COLON
        assert tokens[4].type == TokenType.IDENTIFIER
        assert tokens[4].value == "Person"
        assert tokens[5].type == TokenType.RPAREN
        assert tokens[6].type == TokenType.EOF

    def test_tokenize_create_with_properties(self):
        lexer = Lexer("CREATE (n:Person {name: 'Alice', age: 30})")
        tokens = lexer.tokenize()
        # Verify key tokens
        assert tokens[0].type == TokenType.CREATE
        assert tokens[4].value == "Person"
        assert tokens[5].type == TokenType.LBRACE
        # name: 'Alice'
        assert tokens[6].value == "name"
        assert tokens[7].type == TokenType.COLON
        assert tokens[8].type == TokenType.STRING
        assert tokens[8].value == "Alice"
        assert tokens[9].type == TokenType.COMMA
        # age: 30
        assert tokens[10].value == "age"
        assert tokens[11].type == TokenType.COLON
        assert tokens[12].type == TokenType.INTEGER
        assert tokens[12].value == 30

    def test_tokenize_match_with_where(self):
        lexer = Lexer("MATCH (n:Person) WHERE n.age > 25")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MATCH
        assert tokens[6].type == TokenType.WHERE
        # n.age
        assert tokens[7].type == TokenType.IDENTIFIER
        assert tokens[7].value == "n"
        assert tokens[8].type == TokenType.DOT
        assert tokens[9].type == TokenType.IDENTIFIER
        assert tokens[9].value == "age"
        assert tokens[10].type == TokenType.GT
        assert tokens[11].type == TokenType.INTEGER
        assert tokens[11].value == 25

    def test_tokenize_relationship_pattern(self):
        lexer = Lexer("(a)-[r:KNOWS]->(b)")
        tokens = lexer.tokenize()
        # (a)
        assert tokens[0].type == TokenType.LPAREN
        assert tokens[1].value == "a"
        assert tokens[2].type == TokenType.RPAREN
        # -[r:KNOWS]->
        assert tokens[3].type == TokenType.DASH
        assert tokens[4].type == TokenType.LBRACKET
        assert tokens[5].value == "r"
        assert tokens[6].type == TokenType.COLON
        assert tokens[7].value == "KNOWS"
        assert tokens[8].type == TokenType.RBRACKET
        assert tokens[9].type == TokenType.ARROW_RIGHT
        # (b)
        assert tokens[10].type == TokenType.LPAREN
        assert tokens[11].value == "b"
        assert tokens[12].type == TokenType.RPAREN


class TestLexerErrors:
    """Test error handling."""

    def test_unterminated_string(self):
        lexer = Lexer('"hello')
        with pytest.raises(CypherSyntaxError) as exc_info:
            lexer.tokenize()
        assert "Unterminated string" in str(exc_info.value)

    def test_unexpected_character(self):
        lexer = Lexer("@#$")
        with pytest.raises(CypherSyntaxError) as exc_info:
            lexer.tokenize()
        assert "Unexpected character" in str(exc_info.value)

    def test_invalid_exclamation_mark(self):
        lexer = Lexer("!")
        with pytest.raises(CypherSyntaxError) as exc_info:
            lexer.tokenize()
        assert "!=" in str(exc_info.value)


class TestLexerWhitespace:
    """Test handling of whitespace."""

    def test_ignore_spaces(self):
        lexer = Lexer("  MATCH   (  n  )  ")
        tokens = lexer.tokenize()
        # Should have MATCH, LPAREN, IDENTIFIER, RPAREN, EOF
        assert len(tokens) == 5

    def test_ignore_newlines_and_tabs(self):
        lexer = Lexer("MATCH\n(n)\t")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.MATCH
        assert tokens[1].type == TokenType.LPAREN
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[3].type == TokenType.RPAREN

    def test_track_line_numbers(self):
        lexer = Lexer("MATCH\n(n)")
        tokens = lexer.tokenize()
        assert tokens[0].line == 1  # MATCH on line 1
        assert tokens[1].line == 2  # ( on line 2
