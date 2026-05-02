DB        = newsassistant
CONTAINER = odoo-newsassistant
SERVICE   = odoo
MODULES   = newsassistant,newsassistant_website,newsassistant_email,newsassistant_blog,newsassistant_strategy_digest
LANGUAGE  = de_CH
ADMIN_LANG = de_CH

PIXABAY_API_KEY ?= $(shell grep ^PIXABAY_API_KEY $(PWD)/.env | cut -d= -f2-)

ODOO_CONF = /etc/odoo/odoo.conf
ODOO_PORT = 18069

DOCKER_RUN = docker run --rm --network opencode \
	-v $(PWD)/addons:/mnt/extra-addons \
	-v $(PWD)/odoo.conf:$(ODOO_CONF):ro \
	-v /home/debian/shared/odoo-src/18.0/oca/queue:/mnt/oca/queue:ro \
	-v /home/debian/shared/odoo-src/18.0/oca/web:/mnt/oca/web:ro \
	--env-file $(PWD)/.env \
	odoo:18.0

# ─────────────────────────────────────────────
# rebuild: full clean slate + init + post-setup
# ─────────────────────────────────────────────
.PHONY: rebuild
rebuild: down drop-db clear-filestore init start post-setup smoke
	@echo "Rebuild complete. URL: https://$(DB).opencode.bruehlmeier.com"

# ────────────────────
# Individual targets
# ────────────────────
.PHONY: down
down:
	docker compose down

.PHONY: drop-db
drop-db:
	docker exec postgres psql -U opencode -d postgres \
		-c 'DROP DATABASE IF EXISTS "$(DB)";'

.PHONY: clear-filestore
clear-filestore:
	docker volume rm -f newsassistant_odoo-data 2>/dev/null || true

.PHONY: init
init:
	docker compose run --rm $(SERVICE) odoo \
		-d $(DB) \
		-i $(MODULES) \
		--load-language=$(LANGUAGE) \
		--stop-after-init \
		-c $(ODOO_CONF)

.PHONY: start
start:
	docker compose up -d
	sleep 8

.PHONY: post-setup
post-setup:
	@printf '%s\n' \
		"env['res.users'].browse(2).write({'lang': '$(ADMIN_LANG)'})" \
		"env.ref('newsassistant.newsassistant_group_admin').write({'users': [(4, 2)]})" \
		"env.ref('newsassistant.newsassistant_group_user').write({'users': [(4, 2)]})" \
		"env['ir.config_parameter'].sudo().set_param('newsassistant_blog.pixabay_api_key', '$(PIXABAY_API_KEY)')" \
		"env.cr.commit()" \
		"print('post-setup done')" \
	| docker compose exec -T $(SERVICE) odoo shell \
		-d $(DB) --http-port=$(ODOO_PORT) -c $(ODOO_CONF)

.PHONY: smoke
smoke:
	@HTTP=$$(curl -s -o /dev/null -w "%{http_code}" \
		https://$(DB).opencode.bruehlmeier.com/web/login); \
	if [ "$$HTTP" = "200" ]; then \
		echo "Smoke test: OK ($$HTTP)"; \
	else \
		echo "Smoke test: FAIL ($$HTTP)"; exit 1; \
	fi

# ────────────────────
# Test targets
# ────────────────────
.PHONY: test
test:
	$(DOCKER_RUN) odoo \
		-d test_$(DB)_$$(date +%s) \
		-i $(MODULES) \
		--test-enable \
		--test-tags=/newsassistant,/newsassistant_website,/newsassistant_email,/newsassistant_blog \
		--stop-after-init \
		--http-port=$(ODOO_PORT) \
		-c $(ODOO_CONF)

.PHONY: test-module
test-module:
	$(DOCKER_RUN) odoo \
		-d test_$(DB)_$$(date +%s) \
		-i $(MODULE) \
		--test-enable \
		--test-tags=/$(MODULE) \
		--stop-after-init \
		--http-port=$(ODOO_PORT) \
		-c $(ODOO_CONF)

# ────────────────────
# Translation targets
# ────────────────────
.PHONY: i18n-update
i18n-update:
	@for mod in newsassistant newsassistant_website newsassistant_email newsassistant_blog; do \
		docker compose exec -T $(SERVICE) odoo \
			-d $(DB) \
			--modules=$$mod \
			--i18n-export=/tmp/$$mod.pot \
			--stop-after-init \
			--http-port=$(ODOO_PORT) \
			-c $(ODOO_CONF); \
		docker compose cp $(SERVICE):/tmp/$$mod.pot /tmp/$$mod.pot; \
		echo "POT extracted: /tmp/$$mod.pot"; \
	done

.PHONY: i18n-install
i18n-install:
	docker compose exec -T $(SERVICE) odoo \
		-d $(DB) \
		-u $(MODULES) \
		--load-language=de_CH,de_DE,fr_FR \
		--stop-after-init \
		--http-port=$(ODOO_PORT) \
		-c $(ODOO_CONF)

# ────────────────────────────────────────────────
# sendmail: inject a test newsletter email
#
#   Usage: make sendmail test@skos.ch
#
# Sends a realistic HTML newsletter from the given
# address to the newsassistant alias via XMLRPC.
# ────────────────────────────────────────────────
# Capture the email address when invoked as: make sendmail user@domain.tld
# Only treat the extra goal as a FROM address if it contains '@'
_SENDMAIL_ARG := $(filter-out sendmail,$(MAKECMDGOALS))
_SENDMAIL_FROM := $(if $(findstring @,$(_SENDMAIL_ARG)),$(_SENDMAIL_ARG),editor@skos.ch)

.PHONY: sendmail
sendmail:
	@scripts/sendmail.py "$(_SENDMAIL_FROM)" "$(DB)"

# Suppress "no rule to make target" for the email address argument
$(if $(findstring @,$(_SENDMAIL_ARG)),$(eval $(_SENDMAIL_ARG):;@:))

# ────────────────────
# Utility
# ────────────────────
.PHONY: logs
logs:
	docker compose logs -f $(SERVICE)

.PHONY: shell
shell:
	docker compose exec $(SERVICE) odoo shell \
		-d $(DB) --http-port=$(ODOO_PORT) -c $(ODOO_CONF)

.PHONY: restart
restart:
	docker compose restart $(SERVICE)
