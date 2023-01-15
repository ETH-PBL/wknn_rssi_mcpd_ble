/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/conn.h>

#include "peer.h"

#define DEFAULT_RANGING_MODE    DM_RANGING_MODE_MCPD


static uint32_t access_address;
static enum dm_ranging_mode ranging_mode = DEFAULT_RANGING_MODE;


void peer_ranging_mode_set(enum dm_ranging_mode mode)
{
	ranging_mode = mode;
}

enum dm_ranging_mode peer_ranging_mode_get(void)
{
	return ranging_mode;
}

int peer_access_address_prepare(void)
{
	bt_addr_le_t addr = {0};
	size_t count = 1;

	bt_id_get(&addr, &count);

	access_address = addr.a.val[0];
	access_address |= addr.a.val[1] << 8;
	access_address |= addr.a.val[2] << 16;
	access_address |= addr.a.val[3] << 24;

	if (access_address == 0) {
		return -EFAULT;
	}

	return 0;
}

uint32_t peer_access_address_get(void) { return access_address; }
