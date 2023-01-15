/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

/** @file
 *  @brief Nordic Distance Measurement sample
 */

#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/byteorder.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <bluetooth/scan.h>

#include <dm.h>
#include "peer.h"

#define DEVICE_NAME             CONFIG_BT_DEVICE_NAME
#define DEVICE_NAME_LEN         (sizeof(DEVICE_NAME) - 1)

#define COMPANY_CODE            0x0059
#define SUPPORT_DM_CODE         0xFF55AA5A

struct adv_mfg_data {
	uint16_t company_code;	    /* Company Identifier Code. */
	uint32_t support_dm_code;   /* To identify the device that supports distance measurement. */
	uint32_t access_address;    /* The access address used to measure the distance. */
} __packed;

static struct adv_mfg_data mfg_data;

struct bt_le_adv_param adv_param_noconn =
	BT_LE_ADV_PARAM_INIT(BT_LE_ADV_OPT_USE_IDENTITY |
			     BT_LE_ADV_OPT_SCANNABLE |
			     BT_LE_ADV_OPT_NOTIFY_SCAN_REQ,
			     BT_GAP_ADV_FAST_INT_MIN_1,
			     BT_GAP_ADV_FAST_INT_MAX_1,
			     NULL);


struct bt_le_adv_param *adv_param = &adv_param_noconn;

// advertising data
static const struct bt_data ad[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
	BT_DATA(BT_DATA_NAME_COMPLETE, DEVICE_NAME, DEVICE_NAME_LEN),
};

// scan response packet, needed for DM
static const struct bt_data sd[] = {
	BT_DATA(BT_DATA_MANUFACTURER_DATA, (unsigned char *)&mfg_data, sizeof(mfg_data)),
};

// scan parameters
static struct bt_le_scan_param scan_param = {
	.type     = BT_LE_SCAN_TYPE_ACTIVE,
	.interval = BT_GAP_SCAN_FAST_INTERVAL,
	.window   = BT_GAP_SCAN_FAST_WINDOW,
	.options  = BT_LE_SCAN_OPT_NONE,
	.timeout  = 0,
};

// scan init parameters
static struct bt_scan_init_param scan_init = {
	.connect_if_match = 0,
	.scan_param = &scan_param,
	.conn_param = NULL
};

static struct bt_le_ext_adv *adv;

static struct bt_scan_manufacturer_data scan_mfg_data = {
	.data = (unsigned char *)&mfg_data,
	.data_len = sizeof(mfg_data.company_code) + sizeof(mfg_data.support_dm_code),
};

static bool data_cb(struct bt_data *data, void *user_data)
{
	struct adv_mfg_data *recv_mfg_data;
	struct dm_request req;

	switch (data->type) {
	case BT_DATA_MANUFACTURER_DATA:
		if (sizeof(struct adv_mfg_data) == data->data_len) {
			recv_mfg_data = (struct adv_mfg_data *)data->data;

			bt_addr_le_copy(&req.bt_addr, user_data);
			req.role = DM_ROLE_INITIATOR;
			req.ranging_mode = peer_ranging_mode_get();
			req.access_address = sys_le32_to_cpu(recv_mfg_data->access_address);
			req.start_delay_us = 0;

			dm_request_add(&req);
		}
		return false;
	default:
		return true;
	}
}

static void scan_filter_match(struct bt_scan_device_info *device_info,
			      struct bt_scan_filter_match *filter_match,
			      bool connectable)
{
	bt_addr_le_t addr;

	bt_addr_le_copy(&addr, device_info->recv_info->addr);
	peer_supported_add(device_info->recv_info->addr);
	bt_data_parse(device_info->adv_data, data_cb, &addr);
}

BT_SCAN_CB_INIT(scan_cb, scan_filter_match, NULL, NULL, NULL);

static void adv_scanned_cb(struct bt_le_ext_adv *adv,
			struct bt_le_ext_adv_scanned_info *info)
{
	struct dm_request req;

	if (peer_supported_test(info->addr)) {
		bt_addr_le_copy(&req.bt_addr, info->addr);
		req.role = DM_ROLE_REFLECTOR;
		req.ranging_mode = peer_ranging_mode_get();
		req.access_address = peer_access_address_get();
		req.start_delay_us = 0;

		dm_request_add(&req);
	}
}

const static struct bt_le_ext_adv_cb adv_cb = {
	.scanned = adv_scanned_cb,
};

static int adv_start(void)
{
	int err;
	struct bt_le_ext_adv_start_param ext_adv_start_param = {0};

	if (adv) {
		err = bt_le_ext_adv_stop(adv);
		if (err) {
			printk("Failed to stop extended advertising  (err %d)\n", err);
			return err;
		}
			err = bt_le_ext_adv_delete(adv);
		if (err) {
			printk("Failed to delete advertising set  (err %d)\n", err);
			return err;
		}
	}

	err = bt_le_ext_adv_create(adv_param, &adv_cb, &adv);
	if (err) {
		printk("Failed to create advertising set (err %d)\n", err);
		return err;
	}

	err = bt_le_ext_adv_set_data(adv, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
	if (err) {
		printk("Failed setting adv data (err %d)\n", err);
		return err;
	}

	err = bt_le_ext_adv_start(adv, &ext_adv_start_param);
	if (err) {
		printk("Failed to start extended advertising  (err %d)\n", err);
		return err;
	}

	return err;
}

static int scan_start(void)
{
	int err;

	bt_scan_init(&scan_init);
	bt_scan_cb_register(&scan_cb);

	err = bt_scan_filter_add(BT_SCAN_FILTER_TYPE_MANUFACTURER_DATA, &scan_mfg_data);
	if (err) {
		printk("Scanning filters cannot be set (err %d)\n", err);
		return err;
	}

	err = bt_scan_filter_enable(BT_SCAN_MANUFACTURER_DATA_FILTER, false);
	if (err) {
		printk("Filters cannot be turned on (err %d)\n", err);
		return err;
	}

	err = bt_scan_start(BT_SCAN_TYPE_SCAN_ACTIVE);
	if (err) {
		printk("Scanning failed to start (err %d)\n", err);
		return err;
	}

	return err;
}


//peer_ranging_mode_set(DM_RANGING_MODE_RTT);
//peer_ranging_mode_set(DM_RANGING_MODE_MCPD);



static int bt_sync_init(void)
{
	/* Synchronisation is based on advertising and scanning modes.
	 * It occurs when SCAN_REQ and SCAN_RESP packets are exchanged.
	 */

	int err;

	printk("DM Bluetooth LE Synchronization initialization\n");

	err = peer_access_address_prepare();
	if (err) {
		printk("Failed to prepare access address (err %d)\n", err);
	}

	mfg_data.company_code = sys_cpu_to_le16(COMPANY_CODE);
	mfg_data.support_dm_code = sys_cpu_to_le32(SUPPORT_DM_CODE);
	mfg_data.access_address = sys_cpu_to_le32(peer_access_address_get());

	err = adv_start();
	if (err) {
		printk("Failed to start advertising (err %d)\n", err);
		return err;
	}

	err = scan_start();
	if (err) {
		printk("Failed to start scanning (err %d)\n", err);
	}

	return err;
}

static void data_ready(struct dm_result *result)
{
	if (result->status) {
		peer_update(result);
	}
}

static struct dm_cb dm_cb = {
	.data_ready = data_ready,
};

void main(void)
{
	int err;

	struct dm_init_param init_param;

	printk("Starting Distance Measurement example\n");

	err = peer_init();
	if (err) {
		printk("Peer init failed (err %d)\n", err);
		return;
	}

	init_param.cb = &dm_cb;

	err = dm_init(&init_param);
	if (err) {
		printk("Distance measurement init failed (err %d)\n", err);
		return;
	}

	err = bt_enable(NULL);
	if (err) {
		printk("Bluetooth init failed (err %d)\n", err);
		return;
	}

	err = bt_sync_init();
	if (err) {
		printk("Synchronisation init failed (err %d)\n", err);
		return;
	}

	for (;;) {
		k_sleep(K_FOREVER);
	}
}
