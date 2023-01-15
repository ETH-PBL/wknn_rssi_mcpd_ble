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

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/addr.h>
#include <dm.h>


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
 *  @retval 0 if the operation was successful, otherwise a (negative) error code.
 */
int peer_access_address_prepare(void);

/** @brief Get the current access address.
 *
 *  @retval Access address value.
 */
uint32_t peer_access_address_get(void);

#ifdef __cplusplus
}
#endif

#endif /* PEER_H_ */
