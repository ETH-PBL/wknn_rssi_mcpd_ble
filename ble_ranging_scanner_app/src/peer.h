/*
 * Copyright (c) 2021 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#ifndef PEER_H_
#define PEER_H_

#ifdef __cplusplus
extern "C" {
#endif

#include <dm.h>
#include <zephyr/bluetooth/addr.h>
#include <zephyr/kernel.h>

/** @brief Testing if the peer is supported.
 *
 *  @param peer Bluetooth LE Device Address.
 *
 *  @retval /a true peer is supported.
 *          /a false peer is not supported.
 */
bool peer_supported_test(const bt_addr_le_t *peer);

/** @brief Add a new supported peer.
 *
 *  @param peer Bluetooth LE Device Address.
 *
 *  @retval 0 if the operation was successful, otherwise a (negative) error
 * code.
 */
int peer_supported_add(const bt_addr_le_t *peer);

/** @brief Set a new Distance Measurement ranging mode.
 *
 *  @param mode Ranging mode.
 */
void peer_ranging_mode_set(enum dm_ranging_mode mode);

/** @brief Get the current ranging mode.
 *
 *  @param None
 *
 *  @retval Ranging mode value.
 */
enum dm_ranging_mode peer_ranging_mode_get(void);

/** @brief Prepare an access address.
 *
 *  @retval 0 if the operation was successful, otherwise a (negative) error
 * code.
 */
int peer_access_address_prepare(void);

/** @brief Get the current access address.
 *
 *  @retval Access address value.
 */
uint32_t peer_access_address_get(void);

/** @brief Initialize the peer management module.
 *
 *  @param None
 *
 *  @retval 0 if the operation was successful, otherwise a (negative) error
 * code.
 */
int peer_init(void);

/** @brief Peer measurement update.
 *
 *  @param result Measurement structure.
 */
void peer_update(struct dm_result *result);

/** @brief Peer update rssi.
 *
 *  @param peer Bluetooth LE Device Address
 *  @param rssi RSSI value
 */
void peer_update_rssi(const bt_addr_le_t *peer, int8_t rssi);

#ifdef __cplusplus
}
#endif

#endif /* PEER_H_ */
