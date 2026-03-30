NAME    = Gomoku
SRCDIR  = src
MAIN    = $(SRCDIR)/main.py
PYTHON  = python3
PIP     = pip3

# Colors and Formatting
RESET_LINE  = \033[2K\r
RED_FLASH   = \033[5;31m
GREEN_LIGHT = \033[1;32m
YELLOW      = \033[1;33m
BLUE        = \033[1;34m
BLUE_LIGHT  = \033[1;36m
CYAN        = \033[1;36m
GREY        = \033[1;30m
NOCOLOR     = \033[0m

.PHONY: all clean fclean re install

all: install
	@printf "$(RESET_LINE)$(GREEN_LIGHT)✓ $(NAME) is ready. Run: ./$(NAME)$(NOCOLOR)\n"
	@printf '#!/bin/bash\ncd "$(shell pwd)/$(SRCDIR)" && $(PYTHON) main.py "$$@"\n' > $(NAME)
	@chmod +x $(NAME)

install:
	@printf "$(RESET_LINE)$(BLUE)→ Checking dependencies$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(BLUE)→ Checking dependencies.$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(BLUE)→ Checking dependencies..$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(BLUE)→ Checking dependencies...$(GREY)"
	@sleep 0.1
	@$(PIP) install pygame --quiet || true
	@printf "$(RESET_LINE)$(GREEN_LIGHT)Environment ready!$(NOCOLOR)\n"

clean:
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/	$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/.	$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/..	$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/...	$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/	$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/.	$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/..	$(GREY)"
	@sleep 0.1
	@printf "$(RESET_LINE)$(RED_FLASH)Cleaning $(NAME) pycache/...	$(GREY)"
	@sleep 0.1
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@printf "$(RESET_LINE)$(GREEN_LIGHT)Cleaned successfully!\n$(NOCOLOR)"

fclean: clean
	@printf "$(RESET_LINE)$(YELLOW)🛑 Removing $(NAME) executable...$(NOCOLOR)\n"
	@rm -f $(NAME)
	@printf "$(RESET_LINE)$(GREEN_LIGHT)✅ Full clean successful!$(NOCOLOR)\n"

re: fclean all
