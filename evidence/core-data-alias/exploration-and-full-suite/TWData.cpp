// SPDX-License-Identifier: Apache-2.0
//
// Copyright © 2017 Trust Wallet.

#include <TrustWalletCore/TWData.h>
#include <TrustWalletCore/TWString.h>
#include <TrezorCrypto/memzero.h>
#include "Data.h"
#include "HexCoding.h"
#include <algorithm>
#include <functional>
#include <stdexcept>
#include <vector>

using namespace TW;

TWData *_Nonnull TWDataCreateWithBytes(const uint8_t *_Nonnull bytes, size_t size) {
    auto* data = new Data();
    data->reserve(size);
    std::copy(bytes, bytes + size, std::back_inserter(*data));
    return data;
}

TWData *_Nonnull TWDataCreateWithSize(size_t size) {
    auto* data = new Data(size, 0);
    return data;
}

TWData *_Nonnull TWDataCreateWithData(TWData *_Nonnull data) {
    auto* other = reinterpret_cast<const Data*>(data);
    auto* copy = new Data(*other);
    return copy;
}

TWData* TWDataCreateWithHexString(const TWString* hex) {
    if (hex == nullptr) {
        return nullptr;
    }
    Data data = parse_hex(std::string(TWStringUTF8Bytes(hex)));
    return TWDataCreateWithBytes(data.data(), data.size());
}

size_t TWDataSize(TWData *_Nonnull data) {
    auto* v = reinterpret_cast<const Data*>(data);
    return v->size();
}

uint8_t *_Nonnull TWDataBytes(TWData *_Nonnull data) {
    auto* v = const_cast<Data*>(reinterpret_cast<const Data*>(data));
    return v->data();
}

void TWDataSet(TWData *_Nonnull data, size_t index, uint8_t byte) {
    auto* v = const_cast<Data*>(reinterpret_cast<const Data*>(data));
    if (v->size() <= index) {
        return;
    }
    (*v)[index] = byte;
}

int TWDataCopyBytes(TWData *_Nonnull data, size_t start, size_t size, uint8_t *_Nonnull output) {
    auto* v = reinterpret_cast<const Data*>(data);
    // Check for overflow and bounds
    if (start >= v->size() || size == 0 || size > v->size() - start) {
        return -1;
    }
    std::copy(std::begin(*v) + start, std::begin(*v) + start + size, output);
    return 0;
}

int TWDataReplaceBytes(TWData *_Nonnull data, size_t start, size_t size, const uint8_t *_Nonnull bytes) {
    auto* v = const_cast<Data*>(reinterpret_cast<const Data*>(data));
    // Check for overflow and bounds
    if (start >= v->size() || size == 0 || size > v->size() - start) {
        return -1;
    }
    std::copy(bytes, bytes + size, std::begin(*v) + start);
    return 0;
}

void TWDataAppendBytes(TWData *_Nonnull data, const uint8_t *_Nonnull bytes, size_t size) {
    auto* v = const_cast<Data*>(reinterpret_cast<const Data*>(data));
    if (size == 0) {
        return;
    }
    const auto originalSize = v->size();
    if (size > v->max_size() - originalSize) {
        throw std::length_error("TWData append exceeds maximum size");
    }
    // Capture an offset before reserve can invalidate a pointer into this data.
    bool aliases = false;
    size_t offset = 0;
    if (originalSize != 0) {
        const auto* begin = v->data();
        const auto* end = begin + originalSize;
        const std::less<const uint8_t*> less;
        aliases = !less(bytes, begin) && less(bytes, end);
        if (aliases) {
            offset = static_cast<size_t>(bytes - begin);
            if (size > originalSize - offset) {
                throw std::out_of_range("TWData append source exceeds data bounds");
            }
        }
    }
    v->reserve(originalSize + size);
    if (aliases) {
        bytes = v->data() + offset;
    }
    for (size_t i = 0; i < size; ++i) {
        v->push_back(bytes[i]);
    }
}

void TWDataAppendByte(TWData *_Nonnull data, uint8_t byte) {
    auto* v = const_cast<Data*>(reinterpret_cast<const Data*>(data));
    v->push_back(byte);
}

void TWDataAppendData(TWData *_Nonnull data, TWData *_Nonnull append) {
    const auto* av = reinterpret_cast<const Data*>(append);
    if (!av->empty()) {
        TWDataAppendBytes(data, av->data(), av->size());
    }
}

void TWDataReverse(TWData *_Nonnull data) {
    auto* v = const_cast<Data*>(reinterpret_cast<const Data*>(data));
    std::reverse(std::begin(*v), std::end(*v));
}

void TWDataReset(TWData *_Nonnull data) {
    auto* v = const_cast<Data*>(reinterpret_cast<const Data*>(data));
    std::fill(std::begin(*v), std::end(*v), 0);
}

void TWDataDelete(TWData *_Nonnull data) {
    auto* vConst = reinterpret_cast<const Data*>(data);
    if (!vConst->empty()) {
        // `const_cast` is safe here despite that the pointer to the data is const
        // but `Data` is not a constant value.
        auto *v = const_cast<Data*>(vConst);
        memzero(v->data(), v->size());
    }
    delete vConst;
}

bool TWDataEqual(TWData *_Nonnull lhs, TWData *_Nonnull rhs) {
    auto* lv = reinterpret_cast<const Data*>(lhs);
    auto* rv = reinterpret_cast<const Data*>(rhs);
    return *lv == *rv;
}
